#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Qeez statistics service module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging
from zlib import crc32

from flask import Flask, _app_ctx_stack, request
from flask.json import jsonify
from redis import StrictRedis


APP = Flask(__name__)
APP.config.update(
    DEBUG=False,
    JSONIFY_PRETTYPRINT_REGULAR=False,
    REDIS={
        'SOCKET': '/tmp/redis.sock',
        'DB': 0,
    },
)
LOG_HNDLR = logging.StreamHandler()
LOG_HNDLR.setLevel(logging.NOTSET if APP.debug else logging.ERROR)
LOG_HNDLR.setFormatter(
    logging.Formatter(
        fmt='%(asctime)s %(name)s'
            ' %(levelname)s %(module)s:%(lineno)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'))
APP.logger.addHandler(LOG_HNDLR)


def _json_response(data_dc, status=200):
    '''Creates HTTP response object with appropriate headers for JSON data
    '''
    resp = jsonify(data_dc.items())
    resp.headers['Server'] = 'Flask'
    resp.status_code = status
    return resp


def _calc_checksum(data):
    '''Calculates CRC32 checksum
    '''
    return '%08x' % crc32(data)


def get_redis():
    '''Instantiates and returns redis client
    '''
    top = _app_ctx_stack.top
    if not hasattr(top, 'redis'):
        top.redis = StrictRedis(
            unix_socket_path=APP.config['REDIS']['SOCKET'],
            db=APP.config['REDIS']['DB'])
    return top.redis


def _save_data(qeez_token, packets):
    '''Parses and saves data packets to redis
    '''
    res_dc = {}
    for packet in packets:
        if isinstance(packet, list) and len(packet) == 2:
            # packet = ('grp_id:loc_id:cmp_id:stp_id:gmr_id',
            #    'ans_val:ans_tim:pts')
            key, val = packet
            res_dc[key] = val

    if res_dc:
        get_redis().hmset('_tokens:' + qeez_token, res_dc)


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


def _process_data(req, qeez_token, multi_data=True):
    '''Processes data packets, returns response objects
    '''
    if not req.json:
        return bad_request(None)
    if multi_data:
        json_data = req.get_json()
    else:
        json_data = [req.get_json()]
    checksum = _calc_checksum(req.data)
    _save_data(qeez_token, json_data)
    return _json_response({
        'error': False,
        'checksum': checksum,
    })


@APP.route('/stats/mput/<qeez_token>', methods=['PUT'])
def stats_mput(qeez_token=None):
    '''PUT view to hahdle multiple packets at a time
    '''
    return _process_data(request, qeez_token, multi_data=True)


@APP.route('/stats/put/<qeez_token>', methods=['PUT'])
def stats_put(qeez_token=None):
    '''PUT view to hahdle one packet at a time
    '''
    return _process_data(request, qeez_token, multi_data=False)


if __name__ == '__main__':
    APP.run(host='127.0.0.1', port=8081)
