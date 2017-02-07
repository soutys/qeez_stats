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

import os


REDIS_SOCKET = os.environ.get('REDIS_SOCKET', '/tmp/redis.sock')


CFG = dict(
    DEBUG=False,
    HOST='127.0.0.1',
    PORT=9100,
    JSONIFY_PRETTYPRINT_REGULAR=False,
    STAT_REDIS={
        'SOCKET': REDIS_SOCKET,
        'DB': 0,
    },
    QUEUE_REDIS={
        'SOCKET': REDIS_SOCKET,
        'DB': 1,
    },
    SAVE_REDIS={
        'SOCKET': REDIS_SOCKET,
        'DB': 2,
    },
    ENV_PREPARE_FN='qeez.api.models.prepare_env',
    STAT_SAVE_FN='qeez.api.models.stat_data_save',
)
