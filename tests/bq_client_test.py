from unittest.mock import patch

import cherrypy
import pytest

import webSync


@pytest.fixture
def bq_config():
    keys = ['bigquery.project', 'bigquery.credentials', 'bigquery.credentials_json']
    saved = {k: cherrypy.config.get(k) for k in keys}
    yield
    for k, v in saved.items():
        if v is None:
            cherrypy.config.pop(k, None)
        else:
            cherrypy.config[k] = v


def test_bq_client_uses_inline_credentials_json(bq_config):
    cherrypy.config.update({
        'bigquery.project': 'tfi-data',
        'bigquery.credentials': '',
        'bigquery.credentials_json': '{"type": "service_account", "project_id": "tfi-data"}',
    })
    with patch('webSync.service_account.Credentials.from_service_account_info') as from_info, \
            patch('webSync.bigquery.Client') as client:
        webSync._get_bq_client()

    (info,), kwargs = from_info.call_args
    assert info == {'type': 'service_account', 'project_id': 'tfi-data'}
    assert kwargs['scopes'] == ['https://www.googleapis.com/auth/bigquery']
    client.assert_called_once_with(credentials=from_info.return_value, project='tfi-data')
