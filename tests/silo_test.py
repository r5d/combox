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

from shutil import copyfile
from os import path, remove

from combox.silo import ComboxSilo
from combox.file import read_file, write_file, hash_file

from tests.utils import get_config, rm_nodedirs, rm_configdir

class TestSilo(object):
    """
    Class that tests the silo.py module.
    """

    @classmethod
    def setup_class(self):
        """Set things up."""

        self.config = get_config()
        self.FILES_DIR = self.config['combox_dir']

        self.LOREM = path.join(self.FILES_DIR,'lorem.txt')
        self.IPSUM = path.join(self.FILES_DIR,'ipsum.txt')
        self.LOREM_IPSUM = path.join(self.FILES_DIR,'lorem-ipsum.txt')


    def test_csilo(self):
        """
        Tests the ComboxSilo class.
        """
        csilo = ComboxSilo(self.config)

        # Test - update
        csilo.update(self.LOREM)
        lorem_content = read_file(self.LOREM)
        lorem_hash = csilo.db.get(self.LOREM)
        assert lorem_hash

        csilo.update(self.IPSUM)
        ipsum_content = read_file(self.IPSUM)
        ipsum_hash = csilo.db.get(self.IPSUM)
        assert ipsum_hash

        lorem_ipsum_content = "%s\n%s" % (lorem_content,
                                          ipsum_content)
        write_file(self.LOREM_IPSUM, lorem_ipsum_content)

        csilo.update(self.LOREM_IPSUM)
        lorem_ipsum_hash = csilo.db.get(self.LOREM_IPSUM)
        assert lorem_ipsum_hash

        assert lorem_ipsum_hash != lorem_hash
        assert lorem_ipsum_hash != ipsum_hash

        # Test - stale
        lorem_ipsum_content = "%s\n%s" % (lorem_ipsum_content,
                                          ipsum_content)
        write_file(self.LOREM_IPSUM, lorem_ipsum_content)

        assert csilo.stale(self.LOREM_IPSUM)
        assert csilo.stale(self.LOREM_IPSUM, hash_file(self.LOREM_IPSUM))
        csilo.update(self.LOREM_IPSUM)
        assert csilo.stale(self.LOREM_IPSUM) is False

        lorem_ipsum_hash_new = csilo.db.get(self.LOREM_IPSUM)
        assert lorem_ipsum_hash_new
        assert lorem_ipsum_hash_new != lorem_ipsum_hash

        # Test - remove
        remove(self.LOREM_IPSUM)
        csilo.remove(self.LOREM_IPSUM)

        # Test - exists
        assert not csilo.exists(self.LOREM_IPSUM)


    @classmethod
    def teardown_class(self):
        """Purge the mess created by this test"""
        csilo = ComboxSilo(self.config)
        csilo.remove(self.LOREM)
        csilo.remove(self.IPSUM)
        rm_nodedirs(self.config)
        rm_configdir()
