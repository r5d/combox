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

from combox.config import (config_cb, get_secret, get_stdin)
from tests.utils import get_input_func


class TestConfig(object):
    """
    Class that tests the config.py module.
    """

    @classmethod
    def setup_class(self):
        """Set things up."""
        self.CONFIG_DIR = path.join('tests', 'test-config')


    def test_config(self):
        "Tests the combox's config function."

        config_dir = self.CONFIG_DIR
        pass_func = lambda: 'topsecret'
        input_func = get_input_func()

        config_cb(config_dir, pass_func, input_func)

        # check if the config yaml file is valid
        config_file = path.join(config_dir, 'config.yaml')
        try:
            config = yaml.load(file(config_file, 'r'))
            print "config: ", config
        except yaml.YAMLError, exc:
            raise AssertionError("Error in configuration file:", exc)


    @classmethod
    def teardown_class(self):
        """Tear everything down."""
        # must delete the created config.yaml
        pass
