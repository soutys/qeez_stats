# -*- coding: utf-8 -*-

'''Qeez statistics config module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging


LOG = logging.getLogger(__name__)

CFG = dict(
    DEBUG=False,
    HOST='127.0.1.1',
    PORT=9999,
    JSONIFY_PRETTYPRINT_REGULAR=False,
    STAT_REDIS={
        'SOCKET': '/dev/null',
        'DB': 0,
    },
    QUEUE_REDIS={
        'SOCKET': '/dev/null',
        'DB': 1,
    },
    SAVE_REDIS={
        'SOCKET': '/dev/null',
        'DB': 2,
    },
)
