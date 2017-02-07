# -*- coding: utf-8 -*-

'''qeez_stat.service test module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import sys
from functools import partial

import flask
import pytest

from qeez_stats import service
from qeez_stats.utils import calc_checksum
from qeez_stats.queues import STAT_ID_FMT

from . import fake_qeez
from .config import CFG
from .commons import get_redis


sys.modules['qeez'] = fake_qeez
sys.modules['qeez.api'] = fake_qeez
sys.modules['qeez.api.models'] = fake_qeez


def setup_module(module):
    from qeez_stats import utils
    module.orig_get_redis = utils.get_redis
    utils.get_redis = get_redis


def teardown_module(module):
    from qeez_stats import utils
    utils.get_redis = module.orig_get_redis
    del module.orig_get_redis


@pytest.fixture
def client(request):
    service.APP.config['TESTING'] = True
    flask_cli = service.APP.test_client()
    # NOTE: a place for some monkey-like patching:
#    with service.APP.app_context():
#        used_module.internal_fn = _patched_internal_fn
    return flask_cli


def test_prepare_env():
    from qeez_stats.config import CFG as _CFG
    _CFG['ENV_PREPARE_FN'] = CFG['ENV_PREPARE_FN']
    service.prepare_env()


def test_not_found(client):
    resp = client.get('/')
    assert flask.json.loads(resp.data) == {'error': True, 'status': 404}


def test_method_not_allowed(client):
    resp = client.get('/stats/mput/123')
    assert flask.json.loads(resp.data) == {'error': True, 'status': 405}


def test_bad_request(client):
    resp = client.put('/stats/mput/123')
    assert flask.json.loads(resp.data) == {'error': True, 'status': 400}


def test_internal_server_error(client):
    with service.APP.app_context():
        resp = service.internal_server_error(None)
        assert flask.json.loads(resp.data) == {'error': True, 'status': 500}


def test_stats_mput_fail(client):
    _data = b'[["1:2:3:4:5:6", "8:9:10"]]'
    resp = client.put(
        '/stats/mput/test_123', data=_data, content_type='application/json')
    assert flask.json.loads(resp.data) == {'error': True, 'status': 400}


def test_stats_mput_ok(client):
    _data = b'[["1:2:3:4:5:6:7", "8:9:10"],' \
        b'["11:12:13:14:15:16:17", "18:19:20"]]'
    checksum = calc_checksum(_data)
    resp = client.put(
        '/stats/mput/test_123', data=_data, content_type='application/json')
    assert flask.json.loads(resp.data) == {'checksum': checksum, 'error': False}


def test_stats_put_fail(client):
    _data = b'["1:2:3:4:5:6", "8:9:10"]'
    checksum = calc_checksum(_data)
    resp = client.put(
        '/stats/put/test_123', data=_data, content_type='application/json')
    assert flask.json.loads(resp.data) == {'error': True, 'status': 400}


def test_stats_put_ok(client):
    _data = b'["1:2:3:4:5:6:7", "8:9:10"]'
    checksum = calc_checksum(_data)
    resp = client.put(
        '/stats/put/test_123', data=_data, content_type='application/json')
    assert flask.json.loads(resp.data) == {'checksum': checksum, 'error': False}


def test_stats_put_ok_direct(client):
    _data = b'["1:2:3:4:5:6:7", "8:9:10"]'
    checksum = calc_checksum(_data)
    resp = client.put(
        '/stats/put/test_123?sync', data=_data, content_type='application/json')
    assert flask.json.loads(resp.data) == {'checksum': checksum, 'error': False}


def test_stats_ar_mput(client):
    _data = b'[["1:2:3:4:5:6:7", "8:9:10"],' \
        b'["11:12:13:14:15:16:17", "18:19:20"]]'
    checksum = calc_checksum(_data)
    stat_id = CFG['STAT_CALC_FN']
    qeez_token = 'test_123'
    resp = client.put(
        '/stats/ar_mput/' + stat_id + '/' + qeez_token, data=_data,
        content_type='application/json')
    assert flask.json.loads(resp.data) == {'checksum': checksum, 'error': False,
        'job_id': STAT_ID_FMT % (stat_id, qeez_token)}


def test_stats_ar_put(client):
    _data = b'["1:2:3:4:5:6:7", "8:9:10"]'
    checksum = calc_checksum(_data)
    stat_id = CFG['STAT_CALC_FN']
    qeez_token = 'test_123'
    resp = client.put(
        '/stats/ar_put/' + stat_id + '/' + qeez_token, data=_data,
        content_type='application/json')
    assert flask.json.loads(resp.data) == {'checksum': checksum, 'error': False,
        'job_id': STAT_ID_FMT % (stat_id, qeez_token)}


def test_stats_proc_enq(client):
    stat_id = CFG['STAT_CALC_FN']
    qeez_token = 'test_123'
    resp = client.put(
        '/stats/proc_enq/' + stat_id + '/' + qeez_token,
        content_type='application/json')
    assert flask.json.loads(resp.data) == {'checksum': '00000000',
        'error': False, 'job_id': STAT_ID_FMT % (stat_id, qeez_token)}


def test_stats_result_get_no_res(client):
    stat_id = CFG['STAT_CALC_FN']
    qeez_token = 'test_123'
    resp = client.get(
        '/stats/result/' + stat_id + '/' + qeez_token,
        content_type='application/json')
    assert flask.json.loads(resp.data) == {'error': False, 'result': None}


def test_stats_results_get_res_ok(client):
    stat_id = CFG['STAT_CALC_FN']
    resp = client.get(
        '/stats/results/' + stat_id,
        content_type='application/json')
    assert flask.json.loads(resp.data) == {'error': False, 'result': [123.1]}
