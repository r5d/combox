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

from shutil import copyfile
from os import path, remove
from threading import Lock

from combox.silo import ComboxSilo
from combox.file import read_file, write_file, hash_file

from nose.tools import *

from tests.utils import get_config, rm_nodedirs, rm_configdir

class TestSilo(object):
    """
    Class that tests the silo.py module.
    """

    @classmethod
    def setup_class(self):
        """Set things up."""

        self.silo_lock = Lock()
        self.config = get_config()
        self.FILES_DIR = self.config['combox_dir']

        self.LOREM = path.join(self.FILES_DIR,'lorem.txt')
        self.IPSUM = path.join(self.FILES_DIR,'ipsum.txt')
        self.LOREM_IPSUM = path.join(self.FILES_DIR,'lorem-ipsum.txt')


    def test_csilo(self):
        """
        Tests the ComboxSilo class.
        """
        csilo = ComboxSilo(self.config, self.silo_lock)

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


    def test_csilo_node_dicts(self):
        """Tests ComboxSilo class, if the dictinaries need for housekeeping
        node directories are created.

        """
        silo = ComboxSilo(self.config, self.silo_lock)
        keys = silo.db.db.keys()

        node_dicts = ['file_created', 'file_modified', 'file_moved',
                      'file_deleted', 'file_moved_info']
        for ndict in node_dicts:
            assert ndict in keys


    def test_csilo_nodset_create(self):
        """Tests node_set method, in ComboxSilo class, when type is 'file_created'.
        """

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.node_set('file_created', self.LOREM)
        silo.node_set('file_created', self.LOREM)
        silo.node_set('file_created', self.LOREM)

        silo.node_set('file_created', self.IPSUM)
        silo.node_set('file_created', self.IPSUM)
        silo.node_set('file_created', self.IPSUM)
        silo.node_set('file_created', self.IPSUM)

        dict_file_created = silo.db.get('file_created')
        assert_equal(3, dict_file_created[self.LOREM])
        assert_equal(4, dict_file_created[self.IPSUM])

        silo.node_set('file_created', self.LOREM, 15)
        dict_file_created = silo.db.get('file_created')
        assert_equal(15, dict_file_created[self.LOREM])


    def test_csilo_nodset_modified(self):
        """Tests node_set method, in ComboxSilo class, when type is 'file_modified'.
        """

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.node_set('file_modified', self.LOREM)
        silo.node_set('file_modified', self.LOREM)
        silo.node_set('file_modified', self.LOREM)

        silo.node_set('file_modified', self.IPSUM)
        silo.node_set('file_modified', self.IPSUM)
        silo.node_set('file_modified', self.IPSUM)
        silo.node_set('file_modified', self.IPSUM)

        dict_file_modified = silo.db.get('file_modified')
        assert_equal(3, dict_file_modified[self.LOREM])
        assert_equal(4, dict_file_modified[self.IPSUM])

        silo.node_set('file_modified', self.LOREM, 15)
        dict_file_modified = silo.db.get('file_modified')
        assert_equal(15, dict_file_modified[self.LOREM])


    def test_csilo_nodset_moved(self):
        """Tests node_set method, in ComboxSilo class, when type is 'file_moved'.
        """

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.node_set('file_moved', self.LOREM)
        silo.node_set('file_moved', self.LOREM)
        silo.node_set('file_moved', self.LOREM)

        silo.node_set('file_moved', self.IPSUM)
        silo.node_set('file_moved', self.IPSUM)
        silo.node_set('file_moved', self.IPSUM)
        silo.node_set('file_moved', self.IPSUM)

        dict_file_moved = silo.db.get('file_moved')
        assert_equal(3, dict_file_moved[self.LOREM])
        assert_equal(4, dict_file_moved[self.IPSUM])

        silo.node_set('file_moved', self.LOREM, 15)
        dict_file_moved = silo.db.get('file_moved')
        assert_equal(15, dict_file_moved[self.LOREM])

    def test_csilo_nodset_file_deleted(self):
        """Tests node_set method in ComboxSilo class, when type is 'file_deleted'.
        """

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.node_set('file_deleted', self.LOREM)
        silo.node_set('file_deleted', self.LOREM)
        silo.node_set('file_deleted', self.LOREM)

        silo.node_set('file_deleted', self.IPSUM)
        silo.node_set('file_deleted', self.IPSUM)
        silo.node_set('file_deleted', self.IPSUM)
        silo.node_set('file_deleted', self.IPSUM)

        dict_file_deleted = silo.db.get('file_deleted')
        assert_equal(3, dict_file_deleted[self.LOREM])
        assert_equal(4, dict_file_deleted[self.IPSUM])

        silo.node_set('file_deleted', self.LOREM, 15)
        dict_file_deleted = silo.db.get('file_deleted')
        assert_equal(15, dict_file_deleted[self.LOREM])


    def test_csilo_node_store_moved_info(self):
        """Tests node_store_moved_info method in ComboxSilo class.
        """
        silo = ComboxSilo(self.config, self.silo_lock)

        src_path  = self.LOREM
        dest_path = self.LOREM_IPSUM
        silo.node_store_moved_info(src_path, dest_path)

        assert_equal(dest_path, silo.node_get('file_moved_info', src_path))


    def test_csilo_nodeget(self):
        """Tests node_get method in ComboxSilo class
        """
        silo = ComboxSilo(self.config, self.silo_lock)
        assert_equal(None, silo.node_get('file_created', self.LOREM))

        silo.node_set('file_created', self.LOREM)
        silo.node_set('file_created', self.LOREM)
        assert_equal(2, silo.node_get('file_created', self.LOREM))


    def test_csilo_noderem(self):
        """Tests node_rem method in ComboxSilo class
        """
        silo = ComboxSilo(self.config, self.silo_lock)

        silo.node_set('file_created', self.LOREM)
        silo.node_set('file_created', self.LOREM)
        silo.node_set('file_created', self.LOREM)
        silo.node_set('file_created', self.LOREM)
        assert_equal(4, silo.node_get('file_created', self.LOREM))

        removed = silo.node_rem('file_created', self.LOREM)
        assert_equal(4, removed)
        assert_equal(None, silo.node_get('file_created', self.LOREM))

    def teardown(self):
        """Cleans up things after each test in this class"""

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.db.deldb()


    @classmethod
    def teardown_class(self):
        """Purge the mess created by this test"""
        csilo = ComboxSilo(self.config, self.silo_lock)
        csilo.remove(self.LOREM)
        csilo.remove(self.IPSUM)
        rm_nodedirs(self.config)
        rm_configdir()
