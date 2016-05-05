#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Qeez statistics service module

$ pip install -U .
$ python -m qeez_stats.service
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging
from time import gmtime

from flask import Flask, _app_ctx_stack, request
from flask.json import jsonify

from qeez_stats.config import CFG
from qeez_stats.queues import (
    enqueue_stat_save,
    enqueue_stat_calc,
    pull_all_stat_res,
    pull_stat_res,
)
from qeez_stats.utils import (
    calc_checksum,
    get_queue_redis,
    get_save_redis,
    get_stat_redis,
    packet_split,
    save_packets_to_stat,
)


APP = Flask(__name__)
APP.config.update(CFG)
LOG_HNDLR = logging.StreamHandler()
LOG_HNDLR.setLevel(logging.NOTSET if APP.debug else logging.ERROR)
LOG_HNDLR.setFormatter(
    logging.Formatter(
        fmt='%(asctime)s %(name)s'
            ' %(levelname)s %(module)s:%(lineno)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'))
APP.logger.addHandler(LOG_HNDLR)

# LOG = logging.getLogger(__name__)


def _json_response(data_dc, status=200):
    '''Creates HTTP response object with appropriate headers for JSON data
    '''
    resp = jsonify(data_dc.items())
    resp.headers['Server'] = 'Flask'
    resp.status_code = status
    return resp


def _save_packets(qeez_token, res_dc):
    '''Saves data packets (to all possible DBs)
    '''
    save_packets_to_stat(qeez_token, res_dc, redis_conn=get_stat_redis())
    enqueue_stat_save(
        qeez_token, res_dc, atime=gmtime(), redis_conn=get_save_redis())


def _save_data(qeez_token, packets):
    '''Parses and saves data packets
    '''
    res_dc = {}
    for packet in packets:
        if isinstance(packet, list) and len(packet) == 2:
            key, val = packet
            if packet_split(key, val):
                res_dc[key] = val

    if res_dc:
        _save_packets(qeez_token, res_dc)
        return True
    return False


@APP.errorhandler(404)
def not_found(_):
    '''HTTP 404 error handler
    '''
    return _json_response({'error': True, 'status': 404}, status=404)


@APP.errorhandler(405)
def method_not_allowed(_):
    '''HTTP 405 error handler
    '''
    return _json_response({'error': True, 'status': 405}, status=405)


@APP.errorhandler(400)
def bad_request(_):
    '''HTTP 400 error handler
    '''
    return _json_response({'error': True, 'status': 400}, status=400)


@APP.errorhandler(500)
def internal_server_error(_):
    '''HTTP 500 error handler
    '''
    return _json_response({'error': True, 'status': 500}, status=500)


def _process_data(req, qeez_token, multi_data=None, stat=None):
    '''Processes data packets, returns response objects
    '''
    if not req.json:
        return bad_request(None)
    _json = req.get_json()
    if multi_data is True:
        json_data = _json
    else:
        json_data = [_json]
    checksum = calc_checksum(req.data)
    if _save_data(qeez_token, json_data):
        resp = {
            'error': False,
            'checksum': checksum}
        if stat is not None:
            job = enqueue_stat_calc(
                stat, qeez_token, redis_conn=get_queue_redis())
            resp['job_id'] = job.id
        return _json_response(resp)
    return bad_request(None)


@APP.route('/stats/mput/<qeez_token>', methods=['PUT'])
def stats_mput(qeez_token=None):
    '''PUT view to handle multiple packets at a time
    '''
    return _process_data(request, qeez_token, multi_data=True, stat=None)


@APP.route('/stats/put/<qeez_token>', methods=['PUT'])
def stats_put(qeez_token=None):
    '''PUT view to handle one packet at a time
    '''
    return _process_data(request, qeez_token, multi_data=False, stat=None)


@APP.route('/stats/ar_mput/<stat>/<qeez_token>', methods=['PUT'])
def stats_ar_mput(stat=None, qeez_token=None):
    '''PUT view to handle multiple packets at a time with auto-recalculation
    '''
    return _process_data(request, qeez_token, multi_data=True, stat=stat)


@APP.route('/stats/ar_put/<stat>/<qeez_token>', methods=['PUT'])
def stats_ar_put(stat=None, qeez_token=None):
    '''PUT view to handle one packet at a time with auto-recalculation
    '''
    return _process_data(request, qeez_token, multi_data=False, stat=stat)


@APP.route('/stats/proc_enq/<stat>/<qeez_token>', methods=['PUT'])
def stats_proc_enq(stat=None, qeez_token=None):
    '''PUT view to enqueue selected stat processing
    '''
    checksum = calc_checksum(request.data)
    job = enqueue_stat_calc(stat, qeez_token, redis_conn=get_queue_redis())
    return _json_response({
        'error': False,
        'checksum': checksum,
        'job_id': job.id,
    })


@APP.route('/stats/result/<stat>/<qeez_token>', methods=['GET'])
def stats_result_get(qeez_token=None, stat=None):
    '''GET view to get selected stat result
    '''
    result = pull_stat_res(stat, qeez_token, redis_conn=get_queue_redis())
    return _json_response({
        'error': False,
        'result': result,
    })


@APP.route('/stats/results/<stat>', methods=['GET'])
def stats_results_get(stat=None):
    '''GET view to get selected stat result
    '''
    result = pull_all_stat_res(stat, redis_conn=get_queue_redis())
    return _json_response({
        'error': False,
        'result': result,
    })


if __name__ == '__main__':
    APP.run(host=APP.config['HOST'], port=APP.config['PORT'])
