#    Copyright (C) 2015 Combox author(s). See AUTHORS.
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

import yaml

from nose.tools import *
from os import path, remove, rmdir

from combox.config import config_cb


def get_input_func():
    """Returns the input function

    The input function is meant to be passed to the config_cb function
    in the combox.config module.

    """
    config_dir = path.join('tests', 'test-config')
    combox_dir = path.join('tests', 'files')
    node_dir_0 = path.join('tests', 'shard-dir-0')
    node_dir_1 = path.join('tests', 'shard-dir-1')

    # sample config info.
    config_info = ['testbox', combox_dir, config_dir, '2',
                   'node-0', node_dir_0, '1024',
                   'node-1', node_dir_1, '1024']

    config_info_iter = iter(config_info)
    input_func = lambda(x): next(config_info_iter)

    return input_func


def get_config():
    """Constructs test config dict and returns it."""

    config_dir = path.join('tests', 'test-config')
    pass_func = lambda: 'topsecret'
    input_func = get_input_func()

    return config_cb(config_dir, pass_func, input_func, write=False)
