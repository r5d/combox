# -*- coding: utf-8 -*-
#
#    Copyright (C) 2016 Dr. Robert C. Green II.
#
#    This file is part of Combox.
#
#   Combox is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Combox is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Combox (see COPYING).  If not, see
#   <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

from combox._version import get_version


def readf(filename):
    with open(filename, 'r') as f:
        return f.read()


config = {
    'name': 'combox',
    'description': 'Encrypts files and scatters them across storage provided by Google Drive and Dropbox.',
    'long_description': readf('README.rst'),
    'version': get_version(),
    'platforms': ['GNU/Linux', 'OS X'],
    'license': 'GNU General Public License version 3 or later',
    'url': 'https://ricketyspace.net/combox/',
    'download_url': 'https://git.ricketyspace.net/combox',
    'author': 'combox contributors',
    'author_email': 'sravik@bgsu.edu',
    'install_requires': ['watchdog', 'PyYAML', 'pycrypto',
                         'simplejson', 'pickledb'],
    'tests_require': ['nose', 'mock'],
    'test_suite': 'nose.collector',
    'packages': find_packages(exclude=['tests']),
    'entry_points': {
        'console_scripts': ['combox = combox.cbox:main']
    },
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Intended Audience :: End Users/Desktop',
        'License :: DFSG approved',
        'License :: OSI Approved',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: Utilities',
        ]
}

setup(**config)
