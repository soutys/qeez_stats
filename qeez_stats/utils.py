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

PACKETS_ID_FMT = '_packets:%s'
PACKET_SEP = b':'


if sys.version_info > (3,):
    def to_bytes(str_buf):
        return bytes(str_buf, encoding='utf-8')

    def to_str(str_buf):
        return str(byte_buf, encoding='utf-8')
else:
    def to_bytes(str_buf):
        return bytes(str_buf)


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
    parts = packet_split(key, val)
    if parts is None:
        return None
    key_parts, val_parts = parts

    # TODO: named tuple
    return (
        tuple(int(part) for part in key_parts),
        (
            val_parts[0].decode('utf-8'),
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
