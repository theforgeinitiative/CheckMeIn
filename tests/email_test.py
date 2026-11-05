import io
import json
import urllib.error
from unittest.mock import patch

import pytest

import utils


@pytest.fixture
def urlopen():
    with patch('urllib.request.urlopen') as mock:
        yield mock


@pytest.fixture
def smtp():
    with patch('smtplib.SMTP') as mock:
        yield mock


def sent_request(urlopen):
    (request,), _ = urlopen.call_args
    return request


def test_uses_resend_when_api_key_set(monkeypatch, urlopen, smtp):
    monkeypatch.setenv('RESEND_API_KEY', 're_test_key')
    utils.sendEmail('Jane Doe', 'jane@example.com', 'Hello', 'Body text')

    request = sent_request(urlopen)
    assert request.full_url == 'https://api.resend.com/emails'
    assert request.get_method() == 'POST'
    assert request.get_header('Authorization') == 'Bearer re_test_key'
    assert request.get_header('Content-type') == 'application/json'
    assert json.loads(request.data) == {
        'from': 'TFI CheckMeIn <noreply@theforgeinitiative.org>',
        'to': ['Jane Doe <jane@example.com>'],
        'subject': 'Hello',
        'text': 'Body text',
    }
    smtp.assert_not_called()


def test_resend_includes_cc(monkeypatch, urlopen):
    monkeypatch.setenv('RESEND_API_KEY', 're_test_key')
    utils.sendEmail('Jane Doe', 'jane@example.com', 'Hello', 'Body',
                    ccName='Ops', ccEmail='ops@example.com')

    payload = json.loads(sent_request(urlopen).data)
    assert payload['cc'] == ['Ops <ops@example.com>']


def test_resend_failure_does_not_raise(monkeypatch, urlopen, capsys):
    monkeypatch.setenv('RESEND_API_KEY', 're_test_key')
    urlopen.side_effect = urllib.error.HTTPError(
        'https://api.resend.com/emails', 403, 'Forbidden', {},
        io.BytesIO(b'{"message": "domain not verified"}'))

    utils.sendEmail('Jane Doe', 'jane@example.com', 'Hello', 'Body')

    assert 'domain not verified' in capsys.readouterr().out


def test_uses_smtp_without_api_key(monkeypatch, urlopen, smtp):
    monkeypatch.delenv('RESEND_API_KEY', raising=False)
    utils.sendEmail('Jane Doe', 'jane@example.com', 'Hello', 'Body')

    smtp.assert_called_once_with('localhost')
    urlopen.assert_not_called()
