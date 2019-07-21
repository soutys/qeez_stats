# -*- coding: utf-8 -*-

'''qeez_stat.queues test module
'''

import sys

from rq.job import Job
from rq.queue import Queue
from rq.worker import SimpleWorker

from qeez_stats import queues

from . import fake_qeez
from .config import CFG
from .commons import get_redis, get_token


sys.modules['qeez'] = fake_qeez
sys.modules['qeez.api'] = fake_qeez
sys.modules['qeez.api.models'] = fake_qeez


def setup_module(module):
    from qeez_stats import utils
    module.queues.orig_q_get_redis = module.queues.get_redis
    module.orig_u_get_redis = utils.get_redis
    utils.get_redis = module.queues.get_redis = get_redis


def teardown_module(module):
    from qeez_stats import utils
    module.queues.get_redis = module.queues.orig_q_get_redis
    utils.get_redis = module.orig_u_get_redis
    del module.queues.orig_q_get_redis
    del module.orig_u_get_redis


def test_direct_stat_save():
    from qeez_stats.config import CFG as _CFG
    qeez_token = get_token()

    orig_stat_save_fn = CFG['STAT_SAVE_FN']
    _CFG['STAT_SAVE_FN'] = CFG['STAT_SAVE_FN'] = \
        'qeez.api.models.stat_data_save2'

    ret = queues.direct_stat_save(qeez_token, {}, atime=None)
    assert isinstance(ret, bool)
    assert not ret

    _CFG['STAT_SAVE_FN'] = CFG['STAT_SAVE_FN'] = \
        'qeez.api2.models.stat_data_save'

    ret = queues.direct_stat_save(qeez_token, {}, atime=None)
    assert isinstance(ret, bool)
    assert not ret

    _CFG['STAT_SAVE_FN'] = CFG['STAT_SAVE_FN'] = \
        'qeez.api.models.stat_data_save_failing'
    from raven import Client
    _CFG['RAVEN_CLI'] = CFG['RAVEN_CLI'] = Client('')

    ret = queues.direct_stat_save(qeez_token, {}, atime=None)
    assert isinstance(ret, bool)
    assert not ret

    _CFG['STAT_SAVE_FN'] = CFG['STAT_SAVE_FN'] = orig_stat_save_fn

    ret = queues.direct_stat_save(None, {}, atime=None)
    assert isinstance(ret, bool)
    assert not ret

    ret = queues.direct_stat_save(qeez_token, {}, atime=None, raise_exc=True)
    assert isinstance(ret, bool)
    assert not ret

    ret = queues.direct_stat_save(qeez_token, {}, atime=None)
    assert isinstance(ret, bool)
    assert ret


def test_enqueue_stat_save():
    qeez_token = get_token()

    job = queues.enqueue_stat_save(qeez_token, {}, atime=None, redis_conn=None)
    assert isinstance(job, Job)
    assert job.id

    job = queues.enqueue_stat_save(
        qeez_token, {}, atime=None, redis_conn=get_redis(CFG['SAVE_REDIS']))
    assert isinstance(job, Job)
    assert job.id


def test_enqueue_stat_calc_fail():
    stat_id = CFG['STAT_CALC_FN']
    qeez_token = get_token()

    job = queues.enqueue_stat_calc(stat_id, qeez_token, redis_conn=None)
    assert isinstance(job, Job)

    job = queues.enqueue_stat_calc(
        stat_id, qeez_token, redis_conn=get_redis(CFG['SAVE_REDIS']))
    assert isinstance(job, Job)


def test_enqueue_stat_calc_ok():
    stat_id = CFG['STAT_CALC_FN']
    qeez_token = get_token()

    job = queues.enqueue_stat_calc(
        stat_id, qeez_token, redis_conn=None)
    assert isinstance(job, Job)
    assert job.id

    job = queues.enqueue_stat_calc(
        stat_id, qeez_token, redis_conn=get_redis(CFG['SAVE_REDIS']))
    assert isinstance(job, Job)
    assert job.id


def test_pull_stat_res_fail():
    assert queues.pull_stat_res(
        get_token(), get_token(), redis_conn=None) is None


def test_pull_stat_res_ok():
    from qeez_stats.utils import save_packets_to_stat
    stat_id = CFG['STAT_CALC_FN']
    qeez_token = get_token()
    res_dc = {
        b'7:6:5:4:3:2:1': b'2,3,1:6.5:4',
        b'1:2:3:4:5:6:7': b'1:2:3',
    }
    save_packets_to_stat(qeez_token, res_dc, redis_conn=None)

    job = queues.enqueue_stat_calc(stat_id, qeez_token, redis_conn=None)
    assert isinstance(job, Job)
    assert job.id

    queue = Queue(name=job.origin, connection=job.connection)
    worker = SimpleWorker([queue], connection=queue.connection)
    worker.work(burst=True)

    res = queues.pull_stat_res(stat_id, qeez_token, redis_conn=None)
    assert isinstance(res, float)
    assert res == 123.1


def test_pull_all_stat_res_fail():
    assert queues.pull_all_stat_res(get_token(), redis_conn=None) is None


def test_pull_all_stat_res_no_job():
    stat_id = CFG['STAT_CALC_FN'] + '2'
    assert queues.pull_all_stat_res(stat_id, redis_conn=None) is None


def test_pull_all_stat_no_res():
    stat_id = CFG['STAT_CALC_FN'] + '2'

    job = queues.enqueue_stat_calc(stat_id, get_token(), redis_conn=None)
    assert isinstance(job, Job)
    assert job.id

    assert queues.pull_all_stat_res(stat_id, redis_conn=None) is None


def test_pull_all_stat_res_ok():
    stat_id = CFG['STAT_CALC_FN']
    qeez_token = get_token()

    redis_conn = get_redis(CFG['QUEUE_REDIS'])
    queue = Queue('calc', connection=redis_conn)
    job_1 = Job.create(
        func=stat_id, timeout=30, result_ttl=7200, ttl=7200,
        id=queues.STAT_ID_FMT % (stat_id, qeez_token), connection=redis_conn)
    queue.enqueue_job(job_1)
    job_2 = Job.create(
        func=stat_id, timeout=30, result_ttl=7200, ttl=7200,
        id=queues.STAT_ID_FMT % (stat_id, qeez_token), connection=redis_conn)
    queue.enqueue_job(job_2)

    worker = SimpleWorker([queue], connection=queue.connection)
    worker.work(burst=True)

    assert queues.pull_all_stat_res(stat_id, redis_conn=redis_conn) == [123.1]
