#    Copyright (C) 2014 Combox author(s). See AUTHORS.
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


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Splits encrypted files between online file storage providers',
    'author': 'Siddharth Ravikumar',
    'url': 'http://rsiddharth.ninth.su/git/cb.git/',
    'download_url': 'http://rsiddharth.ninth.su/git/cb.git/',
    'license': 'GNU General Public License v3.0 or later',
    'author_email': 'sravik@bgsu.edu',
    'version': '0.1.1',
    'install_requires': ['nose', 'watchdog', 'PyYAML', 'pycrypto',
                         'simplejson', 'pickledb'],
    'packages': ['combox'],
    'entry_points': {
        'console_scripts': ['combox = combox.cbox:main']
    },
    'name': 'combox'
    }

setup(**config)
