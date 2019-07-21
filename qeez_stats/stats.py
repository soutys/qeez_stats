# -*- coding: utf-8 -*-

'''Qeez statistics stats module
'''

import logging

from qeez_stats.utils import (
    retrieve_set,
    update_set,
)


LOG = logging.getLogger(__name__)


def stat_collector(stat, stat_token, **_):
    '''Collects stat usage
    '''
    update_set(stat, stat_token)
    return retrieve_set(stat)
