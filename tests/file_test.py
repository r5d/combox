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

import yaml

from hashlib import sha512
from glob import glob
from nose.tools import *
from os import path, remove
from shutil import copyfile

from combox.config import get_nodedirs
from combox.crypto import split_and_encrypt
from combox.file import *
from tests.utils import get_config, rm_nodedirs, rm_configdir, purge


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

        # files that have to be removed at the end of this test class
        # should be appended to this list.
        self.purge_list = []


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
        fcontent = read_file(self.TEST_FILE)
        fhash_0 = hash_file(self.TEST_FILE)
        fhash_1 = hash_file(self.TEST_FILE, fcontent)

        assert fhash_0 == sha512(fcontent).hexdigest()
        assert fhash_1 == sha512(fcontent).hexdigest()


    def test_relativepath(self):
        """
        Tests the relative_path function
        """

        test_file_basename = path.basename(self.TEST_FILE)
        assert test_file_basename == relative_path(self.TEST_FILE,
                                                   self.config)

        split_and_encrypt(self.TEST_FILE, self.config)
        test_file_shard_0 = '%s.shard.0' % test_file_basename
        test_file_shard_0_abspath = path.join(get_nodedirs(self.config)[0],
                                              test_file_shard_0)
        test_file_shard_1 = '%s.shard.1' % test_file_basename
        test_file_shard_1_abspath = path.join(get_nodedirs(self.config)[1],
                                              test_file_shard_1)

        assert test_file_shard_0 == relative_path(test_file_shard_0_abspath,
                                                  self.config, False)
        assert test_file_shard_1 == relative_path(test_file_shard_1_abspath,
                                                  self.config, False)

    def test_cbpath(self):
        """Tests the cb_path function"""
        split_and_encrypt(self.TEST_FILE, self.config)
        test_file_shard_0 = '%s.shard0' % path.basename(self.TEST_FILE)
        test_file_shard_0_abspath = path.join(get_nodedirs(self.config)[0],
                                              test_file_shard_0)
        test_file_shard_1 = '%s.shard1' % path.basename(self.TEST_FILE)
        test_file_shard_1_abspath = path.join(get_nodedirs(self.config)[1],
                                              test_file_shard_1)
        assert self.TEST_FILE == cb_path(test_file_shard_0_abspath,
                                            self.config)
        assert self.TEST_FILE == cb_path(test_file_shard_1_abspath,
                                            self.config)

        # a directory inside combox dir.
        foo_dir = path.join(self.config['combox_dir'], 'foo')
        mk_nodedir(foo_dir, self.config)
        foo_nodedir = path.join(get_nodedirs(self.config)[0],
                                'foo')
        assert foo_dir == cb_path(foo_nodedir, self.config)


    def test_nodepath(self):
        """Tests the node_path function"""
        split_and_encrypt(self.TEST_FILE, self.config)
        test_file_shard_0 = '%s.shard0' % path.basename(self.TEST_FILE)
        test_file_shard_0_abspath = path.join(get_nodedirs(self.config)[0],
                                              test_file_shard_0)

        assert test_file_shard_0_abspath == node_path(self.TEST_FILE,
                                                      self.config,
                                                      isfile=True)


        foo_dir = path.join(self.config['combox_dir'], 'foo')
        foo_nodedir = path.join(get_nodedirs(self.config)[0],
                                'foo')

        assert foo_nodedir == node_path(foo_dir, self.config,
                                        isfile=False)


    def test_nodepaths(self):
        """Tests the node_paths function."""
        nodes = get_nodedirs(self.config)
        node_iter = iter(nodes)

        # test for file shards
        foo = path.join(self.config['combox_dir'], 'foo.txt')
        foo_rel_path = relative_path(foo, self.config)
        foo_shards = node_paths(foo, self.config, True)

        shard_no = 0
        for foo_shard in foo_shards:
            file_shard = '%s.shard%d' % (foo_rel_path, shard_no)
            n_path = path.join(node_iter.next(), file_shard)
            assert_equal(n_path, foo_shard)
            shard_no += 1

        # test for directory inside node_directories
        bar = path.join(self.config['combox_dir'], 'bar')
        bar_rel_path = relative_path(bar, self.config)
        bar_n_paths = node_paths(bar, self.config, False)


        node_iter = iter(nodes)
        for bar_n_path in bar_n_paths:
            b_n_path = path.join(node_iter.next(), bar_rel_path)
            assert_equal(b_n_path, bar_n_path)


    def test_rmpath(self):
        """Tests rm_path function"""
        new_dir = path.join(self.config['combox_dir'], 'fooius')
        os.mkdir(new_dir)
        assert path.isdir(new_dir)

        new_file = path.join(new_dir, 'fooius.ext')
        copyfile(self.TEST_FILE, new_file)
        assert path.isfile(new_file)

        rm_path(new_file)
        assert not path.isfile(new_file)

        rm_path(new_dir)
        assert not path.isdir(new_dir)


    def test_mkdir(self):
        """Tests mk_dir function."""
        new_dir = path.join(self.config['combox_dir'], 'barius')
        mk_dir(new_dir)

        assert path.isdir(new_dir)

        # add it to purge list
        self.purge_list.append(new_dir)


    def test_noofshards(self):
        """Tests the node_paths function."""
        nodes = get_nodedirs(self.config)
        node_iter = iter(nodes)
        lorem = path.join(self.config['combox_dir'], 'lorem.txt')

        # get the shards on the node directories
        split_and_encrypt(lorem, self.config)

        # no. of shards must be equal to no. of node directories.
        assert_equal(no_of_shards(lorem, self.config),
                     len(nodes))

        n_paths = node_paths(lorem, self.config, isfile=True)

        # now remove first shard
        rm_path(n_paths[0])
        # no. of shards must be equal to one less than the no. of node
        # directories.
        assert_equal(no_of_shards(lorem, self.config),
                     len(nodes) - 1)

        # now remove second shard
        rm_path(n_paths[1])
        # no. of shards must be equal to two less than the no. of node
        # directories.
        assert_equal(no_of_shards(lorem, self.config),
                     len(nodes) - 2)


    def teardown(self):
        """Cleans up things after each test in this class."""
        purge(self.purge_list)


    @classmethod
    def teardown_class(self):
        """Purge the mess created by this test."""

        rm_shards(self.TEST_FILE, self.config)
        rm_nodedirs(self.config)
        rm_configdir()
