# -*- coding: utf-8 -*-

'''qeez fake modules / methods mock
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)


def prepare_env(**kwargs):
    '''Stub prepare environment function
    '''
    pass


def stat_data_save(qeez_token, *args, **kwargs):
    '''Stub data save function
    '''
    if kwargs.get('raise_exc'):
        raise RuntimeError('Boo!')
    return bool(qeez_token)


def stat_data_save_failing(qeez_token, *args, **kwargs):
    '''Stub failing data save function
    '''
    raise IOError('Ooops!')


def stat_fn(*args, **kwargs):
    '''Stub stat function
    '''
    return 123.1
