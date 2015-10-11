#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Setup script
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
#    unicode_literals,
    with_statement,
)

import os

#from distutils.core import setup
#from pkgutil import walk_packages
from setuptools import setup, find_packages


WORK_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(WORK_DIR)
os.sys.path.insert(1, WORK_DIR)

PKG_NAME = 'qeez_stats'
PKG_MOD = __import__('qeez_stats')

PKG_AUTHOR_NAME, PKG_AUTHOR_EMAIL = PKG_MOD.__author__.rsplit(' ', 1)
PKG_AUTHOR_EMAIL = PKG_AUTHOR_EMAIL.strip('<>')

PKG_VERSION = PKG_MOD.__version__
PKG_CLASSIFIERS = PKG_MOD.__classifiers__

PKG_INFO = open(os.path.join(WORK_DIR, 'README.rst'), 'r').readlines()
PKG_DESC_SHORT = PKG_INFO[0].strip()
PKG_DESC_LONG = ''.join(PKG_INFO)

PKG_LICENSE_FULL = open(os.path.join(WORK_DIR, 'LICENSE'), 'r').readlines()
PKG_LICENSE_NAME = PKG_LICENSE_FULL[0].strip()

PKG_REQS = open(os.path.join(WORK_DIR, 'requirements.txt')).readlines()


## http://stackoverflow.com/a/12966345
#def find_packages(path='.', prefix=''):
#    yield prefix
#    prefix = prefix + '.'
#    for _, name, ispkg in walk_packages(path, prefix):
#        if ispkg:
#            yield name


setup(
    name=PKG_NAME,
    version=PKG_VERSION,
    author=PKG_AUTHOR_NAME,
    author_email=PKG_AUTHOR_EMAIL,
    url='http://github.com/soutys/' + PKG_NAME,
    maintainer=PKG_AUTHOR_NAME,
    maintainer_email=PKG_AUTHOR_EMAIL,
    description=PKG_DESC_SHORT,
    long_description=PKG_DESC_LONG,
    classifiers=PKG_CLASSIFIERS,
    install_requires=PKG_REQS,
    #packages=list(find_packages(WORK_DIR, PKG_MOD.__name__)),
    packages=find_packages(),
    license=PKG_LICENSE_NAME,
    zip_safe=False,
    include_package_data=True,
    package_data = {
        #PKG_NAME: ['VERSION'],
        '': ['VERSION'],
    },
    keywords='redis statistics',
    test_suite='tests',
)

