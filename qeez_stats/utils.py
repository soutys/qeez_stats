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

import logging
import sys
from zlib import crc32

from redis import StrictRedis

from qeez_stats.config import CFG


LOG = logging.getLogger(__name__)

COLL_ID_FMT = '_coll:%s'
PACKETS_ID_FMT = '_packets:%s'
PACKET_SEP = ':'


if sys.version_info > (3,):
    def to_bytes(str_buf):
        '''Converts UTF-8 string to bytes in Py3
        '''
        return bytes(str_buf, encoding='utf-8')

    def to_str(byte_buf):
        '''Converts bytes to UTF-8 string in Py3
        '''
        return str(byte_buf, encoding='utf-8')
else:
    def to_bytes(str_buf):
        '''Converts UTF-8 string to bytes in Py2
        '''
        return bytes(str_buf)

    def to_str(byte_buf):
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
    return StrictRedis(unix_socket_path=redis_cfg['SOCKET'], db=redis_cfg['DB'])


def packet_split(key, val):
    '''Tests if packet parts are OK, returns splitted parts or None
    packet = ('grp_id:loc_id:cmp_id:stp_id:gmr_id',
        'ans_val:ans_tim:pts')
    '''

    LOG.error(
        'key / val: %s (%s) / %s (%s)', repr(key), repr(type(key)), repr(val),
        repr(type(val)))

    key_parts = key.split(PACKET_SEP)
    if len(key_parts) != 5:
        return None
    if not all([part.isdigit() for part in key_parts]):
        return None

    val_parts = val.split(PACKET_SEP)
    if len(val_parts) != 3:
        return None

    return (key_parts, val_parts)


def decode_raw_packet(raw_packet):
    '''Decodes one raw packet
    '''
    key, val = raw_packet
    if isinstance(key, bytes):
        key = to_str(key)
    if isinstance(val, bytes):
        val = to_str(val)
    parts = packet_split(key, val)
    if parts is None:
        return None
    key_parts, val_parts = tuple(parts)

    # TODO: named tuple
    return (
        tuple(int(part) for part in key_parts),
        (
            val_parts[0],
            float(val_parts[1]),
            int(val_parts[2]),
        ),
    )


def decode_raw_packets(raw_packets):
    '''Decodes multiple raw packets at once
    '''
    return [decode_raw_packet(raw_packet) for raw_packet in raw_packets.items()]


def save_packets(qeez_token, res_dc, redis_conn=None):
    '''Saves packets
    '''
    if redis_conn is None:
        redis_conn = get_redis(CFG['STAT_REDIS'])
    redis_conn.hmset(PACKETS_ID_FMT % qeez_token, res_dc)


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
