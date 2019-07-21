# -*- coding: utf-8 -*-

'''Qeez statistics config module
'''

import os

try:
    from raven import Client
    USE_RAVEN = True
except ImportError:
    USE_RAVEN = False


AUTHS_DIR = os.environ.get('AUTHS_DIR', '.')
os.sys.path.append(AUTHS_DIR)

try:
    from auth_settings import (
        RAVEN_DSN,
    )
except ImportError:
    RAVEN_DSN = None

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
    ENV_PREPARE_FN='qeez.utils.models.prepare_env',
    STAT_SAVE_FN='qeez.api.models.stat_data_save',
    RAVEN_CLI=Client(RAVEN_DSN) if USE_RAVEN and RAVEN_DSN else None,
)
