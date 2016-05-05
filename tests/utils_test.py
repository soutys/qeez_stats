# -*- coding: utf-8 -*-

'''qeez_stat.utils test module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import sys
import string
from random import SystemRandom

import pytest
from redis import StrictRedis

from qeez_stats import utils

from .config import CFG
from .commons import get_redis, get_token


def setup_module(module):
    from qeez_stats import utils
    module.orig_get_redis = utils.get_redis
    utils.get_redis = get_redis
    module.qeez_token = get_token()
    module.stat_token = get_token()
    module.stat_id = get_token()


def teardown_module(module):
    from qeez_stats import utils
    utils.get_redis = module.orig_get_redis
    del module.orig_get_redis


if sys.version_info > (3,):
    def test_to_bytes():
        assert utils.to_bytes('abc') == b'abc'

    def test_to_str():
        assert utils.to_str(b'abc') == 'abc'
else:
    def test_to_bytes():
        assert utils.to_bytes('abc') == 'abc'

    def test_to_str():
        assert utils.to_str('abc') == 'abc'


def test_calc_checksum():
    assert utils.calc_checksum(b'') == '00000000'
    assert utils.calc_checksum(b'12') == '4f5344cd'
    assert utils.calc_checksum(b'1234') == '9be3e0a3'


def test_get_redis():
    try:
        assert isinstance(orig_get_redis(CFG['STAT_REDIS']), StrictRedis)
    except NameError as exc:
        assert exc is None


def test_packet_split():
    assert utils.packet_split('', '') is None
    assert utils.packet_split('1:2:3:4', '') is None
    assert utils.packet_split('a:2:3:4:5:6:7', '') is None
    assert utils.packet_split('1:2:3:4:5:6:7', '1:2') is None
    assert utils.packet_split('1:2:3:4:5:6:7', '1:2:3') == \
        (['1', '2', '3', '4', '5', '6', '7'], ['1', '2', '3'])


def test_decode_raw_packet():
    assert utils.decode_raw_packet(['', '']) is None
    assert utils.decode_raw_packet([b'', b'']) is None
    assert utils.decode_raw_packet([b'1:2:3:4:5:6:7', b'1:2:3']) == \
        ((1, 2, 3, 4, 5, 6, 7), ('1', 2.0, 3))


def test_decode_raw_packets():
    assert utils.decode_raw_packets({'': '', 'a': 'b'}) == [None, None]
    assert utils.decode_raw_packets({b'': b'', b'a': b'b'}) == [None, None]
    assert utils.decode_raw_packets(
        {b'': b'', b'1:2:3:4:5:6:7': b'1:2:3'}) == [None,
            ((1, 2, 3, 4, 5, 6, 7), ('1', 2.0, 3))]

    raw_packets = {b'7:6:5:4:3:2:1': b'2,3,1:6.5:4', b'1:2:3:4:5:6:7': b'1:2:3'}
    dec_packets = [((7, 6, 5, 4, 3, 2, 1), ('2,3,1', 6.5, 4)),
        ((1, 2, 3, 4, 5, 6, 7), ('1', 2.0, 3))]
    for dec_packet in dec_packets:
        assert dec_packet in utils.decode_raw_packets(raw_packets)


def test_save_packets_to_stat():
    res_dcs = [
        {'': '', 'a': 'b'},
        {b'': b'', b'a': b'b'},
        {b'': b'', b'1:2:3:4:5:6:7': b'1:2:3'},
        {b'7:6:5:4:3:2:1': b'2,3,1:6.5:4', b'1:2:3:4:5:6:7': b'1:2:3'},
    ]

    redis_conn = get_redis(CFG['STAT_REDIS'])

    for res_dc in res_dcs:
        try:
            assert utils.save_packets_to_stat(qeez_token, res_dc) is True
        except Exception as exc:
            assert exc is None
        try:
            assert utils.save_packets_to_stat(
                qeez_token, res_dc, redis_conn) is True
        except Exception as exc:
            assert exc is None


def test_retrieve_packets():
    res_dcs = {
        b'': b'',
        b'a': b'b',
        b'1:2:3:4:5:6:7': b'1:2:3',
        b'7:6:5:4:3:2:1': b'2,3,1:6.5:4',
    }

    for redis_conn in [None, get_redis(CFG['STAT_REDIS'])]:
        try:
            packets = utils.retrieve_packets(qeez_token, redis_conn)
            assert sorted(packets.items()) == sorted(res_dcs.items())
        except Exception as exc:
            assert exc is None


def test_update_set():
    for redis_conn in [None, get_redis(CFG['STAT_REDIS'])]:
        try:
            assert utils.update_set(stat_id, stat_token, redis_conn) in [0, 1]
        except Exception as exc:
            assert exc is None


def test_retrieve_set():
    for redis_conn in [None, get_redis(CFG['STAT_REDIS'])]:
        try:
            assert set([utils.to_bytes(stat_token)]) == \
                utils.retrieve_set(stat_id, redis_conn)
        except Exception as exc:
            assert exc is None
