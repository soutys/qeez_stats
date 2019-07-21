# -*- coding: utf-8 -*-

'''test commons module
'''

import string
from random import SystemRandom

import fakeredis
from redis import StrictRedis


SYS_RND = SystemRandom()


class FakeStrictRedis(fakeredis.FakeStrictRedis, StrictRedis):
    '''Fake StrictRedis class
    '''
    pass


def get_redis(_):
    '''Returns fake StrictRedis client instance
    '''
    return FSR


def get_token(chars_set=string.ascii_letters, length=10):
    '''Returns pseudo-random token
    '''
    if length > len(chars_set):
        length = len(chars_set)
    return ''.join(SYS_RND.sample(chars_set, length))


FSR = FakeStrictRedis()
