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

import yaml

from nose.tools import *
from os import path, remove, rmdir

from combox.config import (config_cb, get_secret, get_stdin)


CONFIG_DIR = path.join('tests', 'files', 'config')

# sample config info.
CONFIG_INFO = [CONFIG_DIR, '2',
               'gdrive', 'gdrive/path', '1024',
               'dbox', 'dbox/path', '1024']

CONFIG_INFO_ITER = iter(CONFIG_INFO)

def config_iter(dummy):
    "Iterates through CONFIG_INFO"
    return next(CONFIG_INFO_ITER)

def test_config():
    "Tests the combox's config function."

    config_dir = CONFIG_DIR
    pass_func = lambda: 'topsecret'
    input_func = config_iter

    config_cb(config_dir, pass_func, input_func)

    # check if the config yaml file is valid
    config_file = path.join(CONFIG_DIR, 'config.yaml')
    try:
        config = yaml.load(file(config_file, 'r'))
    except yaml.YAMLError, exc:
        raise AssertionError("Error in configuration file:", exc)

    # remove config dir
    remove(config_file)
    rmdir(CONFIG_DIR)