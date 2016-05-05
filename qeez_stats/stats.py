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

from qeez_stats.utils import (
    decode_raw_packets,
    retrieve_packets,
    retrieve_set,
    update_set,
)


LOG = logging.getLogger(__name__)


def stat_collector(stat, stat_token):
    '''Collects stat usage
    '''
    update_set(stat, stat_token)
    return retrieve_set(stat)
