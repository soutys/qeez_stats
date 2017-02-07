# -*- coding: utf-8 -*-

'''Qeez statistics queue module

* queue monitors:
$ rq-dashboard --redis_url=unix:///tmp/redis.sock?db=1 \
    --bind=127.0.0.1 --port=9181 --interval=5000
or
$ rqinfo --url unix:///tmp/redis.sock?db=1

* queue worker:
$ rqworker --url unix:///tmp/redis.sock?db=1 --name my-worker-nr-x --verbose
# or
# python manage.py rqworker --name=my-worker-nr-x queue-of-db-1
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging
from time import gmtime

from rq import Queue

from qeez_stats.config import CFG
from qeez_stats.stats import stat_collector
from qeez_stats.utils import get_method_by_path, get_redis, to_str


LOG = logging.getLogger(__name__)

COLL_ID_FMT = 'stat:%s'
STAT_ID_FMT = 'stat:%s:%s'


def direct_stat_save(qeez_token, res_dc, atime=None, **kwargs):
    '''Saves stat using write method
    '''
    if atime is None:
        atime = gmtime()
    try:
        function = get_method_by_path(CFG['STAT_SAVE_FN'])
        if function:
            return function(qeez_token, atime, res_dc, **kwargs)
    except Exception as exc:
        print(repr(exc))
        LOG.error('%s @ %s', repr(exc), repr(res_dc))

    return False


def enqueue_stat_save(qeez_token, res_dc, atime=None, redis_conn=None):
    '''Enqueues stat for save
    '''
    if atime is None:
        atime = gmtime()
    if redis_conn is None:
        redis_conn = get_redis(CFG['SAVE_REDIS'])
    queue = Queue('save', connection=redis_conn)
    return queue.enqueue(
        CFG['STAT_SAVE_FN'], args=(qeez_token, atime, res_dc),
        timeout=30, result_ttl=30, ttl=-1)


def enqueue_stat_calc(stat, qeez_token, redis_conn=None):
    '''Enqueues stat for calc
    '''
    if redis_conn is None:
        redis_conn = get_redis(CFG['QUEUE_REDIS'])
    stat_token = STAT_ID_FMT % (stat, qeez_token)
    queue = Queue('calc', connection=redis_conn)
    stat_append = queue.enqueue(
        stat_collector, stat, stat_token, timeout=30, result_ttl=-1,
        ttl=-1, job_id=COLL_ID_FMT % stat)
    _ = stat_append.id
    return queue.enqueue(
        stat, qeez_token, timeout=30, result_ttl=-1,
        ttl=-1, job_id=stat_token, depends_on=stat_append)


def pull_stat_res(stat, qeez_token, redis_conn=None):
    '''Pulls one stat's result
    '''
    if redis_conn is None:
        redis_conn = get_redis(CFG['QUEUE_REDIS'])
    queue = Queue('calc', connection=redis_conn)
    job = queue.fetch_job(STAT_ID_FMT % (stat, qeez_token))
    res = None
    if job is not None:
        res = job.result
    if res is not None:
        job.ttl = job.result_ttl = 24 * 3600
        job.save()
    return res


def pull_all_stat_res(stat, redis_conn=None):
    '''Pulls all stat results
    '''
    if redis_conn is None:
        redis_conn = get_redis(CFG['QUEUE_REDIS'])
    queue = Queue('calc', connection=redis_conn)
    job = queue.fetch_job(COLL_ID_FMT % stat)

    res = None
    if job is None:
        return
    res = job.result
    if res is None:
        return

    out = []
    for stat_token in res:
        _job = queue.fetch_job(to_str(stat_token))
        _res = None
        if _job is not None:
            _res = _job.result
        if _res is not None:
            out.append(_res)

    return out
