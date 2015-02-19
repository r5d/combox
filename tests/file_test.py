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

from hashlib import sha512
from glob import glob
from nose.tools import *
from os import path, remove

from combox.config import get_nodedirs
from combox.crypto import split_and_encrypt
from combox.file import *
from tests.utils import get_config, rm_nodedirs, rm_configdir


class TestFile(object):
    """
    Class that tests the file.py module.
    """

    @classmethod
    def setup_class(self):
        """Set things up."""

        self.config = get_config()
        FILES_DIR = self.config['combox_dir']
        self.TEST_FILE = path.join(FILES_DIR,'the-red-star.jpg')


    def test_split(self):
        """Test to split, glue and create a copy of the image file from the
        glued image file.
        """
        f = path.abspath(self.TEST_FILE)
        f_content = read_file(f)
        f_parts = split_data(f_content, 5)
        f_content_glued = glue_data(f_parts)

        assert f_content == f_content_glued


    def test_shards(self):
        """Split file into N shards, write them to disk, glue them together
        and check if they're the same as the orginal file.

        """

        # no. of shards = no. of nodes
        SHARDS = len(self.config['nodes_info'].keys())

        f = path.abspath(self.TEST_FILE)
        f_content = read_file(f)
        f_shards = split_data(f_content, SHARDS)

        f_basename = path.basename(f)
        nodes = get_nodedirs(self.config)
        write_shards(f_shards, nodes, f_basename)

        # check if the shards have been created.
        i = 0
        for node in nodes:
            shard = "%s.shard%s" % (path.join(node, f_basename), i)
            i += 1
            assert path.isfile(shard)

        f_shards = read_shards(nodes, f_basename)
        f_content_glued = glue_data(f_shards)
        assert f_content == f_content_glued


    def test_hashing(self):
        """
        Tests the hashing function - hash_file
        """
        fhash = hash_file(self.TEST_FILE)
        fcontent = read_file(self.TEST_FILE)

        assert fhash == sha512(fcontent).hexdigest()


    def test_relativepath(self):
        """
        Tests the relative_path function
        """

        test_file_basename = path.basename(self.TEST_FILE)
        print test_file_basename
        assert test_file_basename == relative_path(self.TEST_FILE,
                                                   self.config)

        split_and_encrypt(self.TEST_FILE, self.config)
        test_file_shard_0 = '%s.shard.0' % test_file_basename
        test_file_shard_0_abspath = "%s/%s" % (get_nodedirs(self.config)[0],
                                          test_file_shard_0)

        assert test_file_shard_0 == relative_path(test_file_shard_0_abspath,
                                                  self.config, False)


    @classmethod
    def teardown_class(self):
        """Purge the mess created by this test."""

        rm_shards(self.TEST_FILE, self.config)
        rm_nodedirs(self.config)
        rm_configdir()
