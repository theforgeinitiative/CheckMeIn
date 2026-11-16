from unittest.mock import patch

import cherrypy
import pytest

import webSync


@pytest.fixture
def bq_config():
    keys = ['bigquery.project', 'bigquery.credentials_json']
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
        'bigquery.credentials_json': '{"type": "service_account", "project_id": "tfi-data"}',
    })
    with patch('webSync.service_account.Credentials.from_service_account_info') as from_info, \
            patch('webSync.bigquery.Client') as client:
        webSync._get_bq_client()

    (info,), kwargs = from_info.call_args
    assert info == {'type': 'service_account', 'project_id': 'tfi-data'}
    assert kwargs['scopes'] == ['https://www.googleapis.com/auth/bigquery']
    client.assert_called_once_with(credentials=from_info.return_value, project='tfi-data')


def test_bq_client_uses_default_credentials_without_json(bq_config):
    cherrypy.config.update({
        'bigquery.project': 'tfi-data',
        'bigquery.credentials_json': '',
    })
    with patch('webSync.bigquery.Client') as client:
        webSync._get_bq_client()

    client.assert_called_once_with(project='tfi-data')


def test_try_sync_roles_skips_when_unconfigured(bq_config):
    cherrypy.config.update({'bigquery.project': ''})
    with patch('webSync.sync_roles') as sync:
        webSync.try_sync_roles(None)
    sync.assert_not_called()


def test_try_sync_roles_swallows_errors(bq_config):
    cherrypy.config.update({'bigquery.project': 'tfi-data'})
    with patch('webSync.sync_roles', side_effect=RuntimeError('BigQuery down')) as sync:
        webSync.try_sync_roles('db')
    sync.assert_called_once_with('db')
