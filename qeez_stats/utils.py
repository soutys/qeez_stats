# -*- coding: utf-8 -*-

'''Qeez statistics utils module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import importlib
import inspect
import logging
import sys
from zlib import crc32

from redis import StrictRedis

from qeez_stats.config import CFG


LOG = logging.getLogger(__name__)

COLL_ID_FMT = '_coll:%s'
PACKETS_ID_FMT = '_packets:%s'
PACKET_EXPIRE = 1800
PACKET_SEP = ':'
REDIS_CONNS = {}


if sys.version_info > (3,):
    def to_bytes(str_buf):  # pragma: PY2to3
        '''Converts UTF-8 string to bytes in Py3
        '''
        return bytes(str_buf, encoding='utf-8')

    def to_str(byte_buf):  # pragma: PY2to3
        '''Converts bytes to UTF-8 string in Py3
        '''
        return str(byte_buf, encoding='utf-8')
else:
    def to_bytes(str_buf):  # pragma: PY2to3
        '''Converts UTF-8 string to bytes in Py2
        '''
        return bytes(str_buf)

    def to_str(byte_buf):  # pragma: PY2to3
        '''Converts bytes to UTF-8 string in Py2
        '''
        return str(byte_buf)


def calc_checksum(data):
    '''Calculates CRC32 checksum

    NOTE: Generates the same value across all Python versions and platforms.
    '''
    return '%08x' % (crc32(data) & 0xffffffff)


def get_redis(redis_cfg):
    '''Returns redis client instance for a given config
    '''
    return StrictRedis(
        unix_socket_path=redis_cfg['SOCKET'], db=redis_cfg['DB'])


def get_queue_redis():
    '''Instantiates and returns queue redis client
    '''
    if 'queue_redis' not in REDIS_CONNS:
        REDIS_CONNS['queue_redis'] = get_redis(CFG['QUEUE_REDIS'])
    return REDIS_CONNS['queue_redis']


def get_save_redis():
    '''Instantiates and returns save redis client
    '''
    if 'save_redis' not in REDIS_CONNS:
        REDIS_CONNS['save_redis'] = get_redis(CFG['SAVE_REDIS'])
    return REDIS_CONNS['save_redis']


def get_stat_redis():
    '''Instantiates and returns stat redis client
    '''
    if 'stat_redis' not in REDIS_CONNS:
        REDIS_CONNS['stat_redis'] = get_redis(CFG['STAT_REDIS'])
    return REDIS_CONNS['stat_redis']


def packet_split(key, val, rst='0'):
    '''Tests if packet parts are OK, returns splitted parts or None
    packet = ('grp_id:loc_id:cmp_id:rnd_id:cat_id:stp_id:gmr_id:tm_id',
        'ans_val:ans_tim:pts', '[int:int:...]')
    '''

    LOG.debug(
        'key / val / rst: %s (%s) / %s (%s) / %s (%s)',
        repr(key), repr(type(key)),
        repr(val), repr(type(val)),
        repr(rst), repr(type(rst)))

    key_parts = key.split(PACKET_SEP)
    if len(key_parts) != 8:
        LOG.warning('Bad key: %s', repr(key))
        return None
    if not all([part.isdigit() for part in key_parts]):
        LOG.warning('Bad key parts: %s', repr(key_parts))
        return None

    val_parts = val.split(PACKET_SEP)
    if len(val_parts) != 3:
        LOG.warning('Bad val: %s', repr(val))
        return None

    rst_parts = rst.split(PACKET_SEP)
    if not all([part.isdigit() for part in rst_parts]):
        LOG.warning('Bad rst parts: %s', repr(rst_parts))
        return None

    return (key_parts, val_parts, rst_parts)


def decode_raw_packet(raw_packet):
    '''Decodes one raw packet
    '''
    if not raw_packet:
        return None
    raw_packet_len = len(raw_packet)
    if raw_packet_len == 2:
        key, val = raw_packet
        rst = '0'
    elif raw_packet_len == 3:
        key, val, rst = raw_packet
    else:
        return None
    if isinstance(key, bytes):
        key = to_str(key)
    if isinstance(val, bytes):
        val = to_str(val)
    if isinstance(rst, bytes):
        rst = to_str(rst)
    parts = packet_split(key, val, rst)
    if parts is None:
        return None
    key_parts, val_parts, rst_parts = tuple(parts)

    return (
        tuple(int(part) for part in key_parts),
        (
            [int(ans) for ans in val_parts[0].split(',') if ans.isdigit()],
            float(val_parts[1]),
            int(val_parts[2]),
        ),
        tuple(int(part) for part in rst_parts),
    )


def decode_raw_packets(raw_packets):
    '''Decodes multiple raw packets at once
    '''
    return [
        decode_raw_packet(raw_packet) for raw_packet in raw_packets]


def save_packets_to_stat(qeez_token, res_dc, redis_conn=None):
    '''Saves packets
    '''
    if redis_conn is None:
        redis_conn = get_redis(CFG['STAT_REDIS'])
    key = PACKETS_ID_FMT % qeez_token
    res = redis_conn.hmset(key, res_dc)
    redis_conn.expire(key, PACKET_EXPIRE)
    return res


def retrieve_packets(qeez_token, redis_conn=None):
    '''Retrieves packets
    '''
    if redis_conn is None:
        redis_conn = get_redis(CFG['STAT_REDIS'])
    return redis_conn.hgetall(PACKETS_ID_FMT % qeez_token)


def update_set(stat, stat_token, redis_conn=None):
    '''Updates stats' collector set
    '''
    if redis_conn is None:
        redis_conn = get_redis(CFG['STAT_REDIS'])
    return redis_conn.sadd(COLL_ID_FMT % stat, stat_token)


def retrieve_set(stat, redis_conn=None):
    '''Retrieves stats' collector set
    '''
    if redis_conn is None:
        redis_conn = get_redis(CFG['STAT_REDIS'])
    return redis_conn.smembers(COLL_ID_FMT % stat)


def get_method_by_path(method_path):
    '''Returns save method object by path
    '''
    method_mod, method_name = method_path.rsplit('.', 1)
    try:
        importlib.import_module(method_mod)
    except ImportError as exc:
        LOG.error(repr(exc))
        return None
    try:
        mod = sys.modules[method_mod]
        method = eval(method_name, mod.__dict__)
        if inspect.isfunction(method):
            return method
    except (KeyError, NameError) as exc:
        LOG.error(repr(exc))
    return None
