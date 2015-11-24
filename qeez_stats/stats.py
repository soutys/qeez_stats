# -*- coding: utf-8 -*-

'''Qeez statistics stats module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging

from qeez_stats.config import CFG
from qeez_stats.utils import (
    decode_raw_packets,
    retrieve_packets,
)


LOG = logging.getLogger(__name__)


def avg_resp_time(qeez_token):
    '''Calculates average response time
    '''
    raw_packets = retrieve_packets(qeez_token)
    packets = decode_raw_packets(raw_packets)

    resp_time_sum = 0.0
    if not packets:
        return resp_time_sum
    for packet in packets:
        resp_time_sum += packet[1][1]

    return resp_time_sum / len(packets)


def tops_of_locs(qeez_token):
    '''Calculates TOP-10 of locs with % of positive points
    '''
    raw_packets = retrieve_packets(qeez_token)
    packets = decode_raw_packets(raw_packets)

    per_loc = {}
    for packet in packets:
        loc_id = packet[0][1]
        if loc_id in per_loc:
            loc_stat = per_loc[loc_id]
        else:
            loc_stat = per_loc[loc_id] = [0, 0]
        if packet[1][2] > 0:
            loc_stat[0] += 1
        else:
            loc_stat[1] += 1

    locs_stats = {}
    for loc_id, loc_stat in per_loc.items():
        loc_sum = sum(loc_stat)
        if loc_sum:
            locs_stats[loc_id] = int(loc_stat[0] * 100.0 / loc_sum)
        else:
            locs_stats[loc_id] = 0

    return sorted(
        locs_stats.items(),
        key=lambda item: (item[1], item[0]), reverse=True)


STATS_MAP = {
    # per user
    'avg_resp_time': (avg_resp_time, False),
    # loc + % corr answ
    'tops_of_locs': (tops_of_locs, True),
}

# TODO:
# - stats serving end-point
# - stat I/O format agnostic
