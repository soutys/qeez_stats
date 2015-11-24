# -*- coding: utf-8 -*-

'''Qeez statistics queue module

* queue monitors:
$ rq-dashboard --redis_url=unix:///tmp/redis.sock?db=1 \
    --bind=127.0.0.1 --port=9181 --interval=5000
or
$ rqinfo --url unix:///tmp/redis.sock?db=1

* queue worker:
$ rqworker --url unix:///tmp/redis.sock?db=1 --name my-worker-nr-x --verbose
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

from rq import Queue

from qeez_stats.config import CFG
from qeez_stats.stats import STATS_MAP
from qeez_stats.utils import get_redis


STAT_ID_FMT = 'stat:%s:%s'


def enqueue_stat_calc(stat, qeez_token, redis_conn=None):
    '''Enqueues stat for calc
    '''
    if stat not in STATS_MAP:
        return
    if redis_conn is None:
        redis_conn = get_redis(CFG['QUEUE_REDIS'])
    queue = Queue(connection=redis_conn)
    return queue.enqueue_call(
        func=STATS_MAP[stat], args=(qeez_token,), timeout=30, result_ttl=-1,
        ttl=-1, job_id=STAT_ID_FMT % (stat, qeez_token))


def pull_stat_res(stat, qeez_token, redis_conn=None):
    '''Pulls stat's result
    '''
    if stat not in STATS_MAP:
        return
    if redis_conn is None:
        redis_conn = get_redis(CFG['QUEUE_REDIS'])
    queue = Queue(connection=redis_conn)
    job = queue.fetch_job(STAT_ID_FMT % (stat, qeez_token))
    res = job.result
    if res is not None:
        job.ttl = job.result_ttl = 24 * 3600
        job.save()
    return res
