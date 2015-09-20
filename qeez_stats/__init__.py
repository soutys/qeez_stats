# -*- coding: utf-8 -*-

'''Package info module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import os


WORK_DIR = os.path.dirname(os.path.abspath(__file__))

__author__ = 'soutys <soutys@github>'
__version__ = open(os.path.join(WORK_DIR, 'VERSION'), 'r').read().strip()
__classifiers__ = [
    # 'Development Status :: 1 - Planning',
    # 'Development Status :: 2 - Pre-Alpha',
    'Development Status :: 3 - Alpha',
    # 'Development Status :: 4 - Beta',
    # 'Development Status :: 5 - Production/Stable',
    # 'Development Status :: 6 - Mature',
    # 'Development Status :: 7 - Inactive',
    'Environment :: Other Environment',
    'Intended Audience :: Developers',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
    'Topic :: Utilities',
]
