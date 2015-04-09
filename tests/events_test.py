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

import os
import time
import yaml

from filecmp import cmp
from glob import glob
from os import path, remove
from shutil import copyfile
from threading import Lock

from nose.tools import *
from watchdog.observers import Observer

from combox.config import get_nodedirs
from combox.crypto import decrypt_and_glue, split_and_encrypt
from combox.events import ComboxDirMonitor, NodeDirMonitor
from combox.file import (relative_path, purge_dir, hash_file,
                         read_file, write_file, move_shards,
                         rm_shards, mk_nodedir, rm_nodedir,
                         move_nodedir)

from combox.silo import ComboxSilo
from tests.utils import (get_config, shardedp, dirp, renamedp,
                         path_deletedp, rm_nodedirs, rm_configdir,
                         purge_nodedirs, purge)


class TestEvents(object):
    """
    Class that tests the events.py module.
    """

    @classmethod
    def setup_class(self):
        """Set things up."""

        self.silo_lock = Lock()
        self.nodem_lock = Lock()
        self.config = get_config()
        self.silo = ComboxSilo(self.config, self.silo_lock)

        self.FILES_DIR = self.config['combox_dir']
        self.NODE_DIR = get_nodedirs(self.config)[0]
        self.TEST_FILE = path.join(self.FILES_DIR, 'thgttg-21st.png')

        self.lorem = path.join(self.FILES_DIR, 'lorem.txt')
        self.ipsum = path.join(self.FILES_DIR, 'ipsum.txt')
        self.lorem_moved = path.join(self.FILES_DIR, 'lorem.moved.txt')
        self.lorem_ipsum = path.join(self.FILES_DIR, 'lorem.ipsum.txt')

        # files that have to be removed at the end of this test class
        # should be appended to this list.
        self.purge_list = []

    def test_CDM(self):
        """
        Tests the ComboxDirMonitor class.
        """

        event_handler = ComboxDirMonitor(self.config, self.silo_lock)
        observer = Observer()
        observer.schedule(event_handler, self.FILES_DIR, recursive=True)
        observer.start()

        # Test - new file addition
        self.TEST_FILE_COPY_0 = "%s.mutant" % self.TEST_FILE
        copyfile(self.TEST_FILE, self.TEST_FILE_COPY_0)
        ## wait for ComboxDirMonitor to split and scatter the file in the
        ## node directories.
        time.sleep(1)
        ## check if the shards were created.
        shardedp(self.TEST_FILE_COPY_0)
        ## check if the new file's info is in silo
        silo = ComboxSilo(self.config, self.silo_lock)
        assert silo.exists(self.TEST_FILE_COPY_0)

        # Test - File deletion.
        remove(self.TEST_FILE_COPY_0)
        time.sleep(1)
        path_deletedp(self.TEST_FILE_COPY_0)
        ## check if the new file's info is removed from silo
        silo = ComboxSilo(self.config, self.silo_lock)
        assert not silo.exists(self.TEST_FILE_COPY_0)

        # Test - directory creation
        self.TEST_DIR_0 = path.join(self.FILES_DIR, 'foo')
        os.mkdir(self.TEST_DIR_0)
        time.sleep(1)
        ## check if TEST_DIR_0 is created under node directories.
        dirp(self.TEST_DIR_0)

        self.TEST_DIR_1 = path.join(self.TEST_DIR_0, 'bar')
        os.mkdir(self.TEST_DIR_1)
        time.sleep(1)
        ## check if TEST_DIR_1 is created under node directories.
        dirp(self.TEST_DIR_1)

        # Test - new file in a nested directory
        self.TEST_FILE_COPY_1 = path.join(self.TEST_DIR_1,
                                          path.basename(self.TEST_FILE))
        copyfile(self.TEST_FILE, self.TEST_FILE_COPY_1)
        time.sleep(1)
        shardedp(self.TEST_FILE_COPY_1)

        # Test - dir rename
        self.TEST_DIR_1_NEW = path.join(path.dirname(self.TEST_DIR_1),
                                        'snafu')
        self.TEST_FILE_COPY_1_NEW = path.join(self.TEST_DIR_1_NEW,
                                         path.basename(self.TEST_FILE))

        os.rename(self.TEST_DIR_1, self.TEST_DIR_1_NEW)
        time.sleep(1)
        renamedp(self.TEST_DIR_1, self.TEST_DIR_1_NEW)
        renamedp(self.TEST_FILE_COPY_1, self.TEST_FILE_COPY_1_NEW)
        ## check if the new file's info is updated in silo
        silo = ComboxSilo(self.config, self.silo_lock)
        assert not silo.exists(self.TEST_FILE_COPY_1)
        assert silo.exists(self.TEST_FILE_COPY_1_NEW)

        # Test directory & file deletion
        purge_dir(self.TEST_DIR_0)
        # remove the directory itself.
        os.rmdir(self.TEST_DIR_0)
        time.sleep(1)
        path_deletedp(self.TEST_FILE_COPY_1_NEW)
        path_deletedp(self.TEST_DIR_1, True)
        path_deletedp(self.TEST_DIR_0, True)


        # Test - file modification
        self.lorem_file = path.join(self.FILES_DIR, 'lorem.txt')
        self.lorem_file_copy = "%s.copy" % self.lorem_file
        # this will shard lorem.txt.copy in the node directories.
        copyfile(self.lorem_file, self.lorem_file_copy)
        time.sleep(1)
        shardedp(self.lorem_file_copy)
        ## check if the lorem_file_copy's info is stored in silo
        silo = ComboxSilo(self.config, self.silo_lock)
        lorem_file_copy_hash = silo.db.get(self.lorem_file_copy)

        self.ipsum_file = path.join(self.FILES_DIR, 'ipsum.txt')
        ipsum_content = read_file(self.ipsum_file)
        lorem_copy_content = read_file(self.lorem_file_copy)
        lorem_copy_content = "%s\n%s" % (lorem_copy_content, ipsum_content)

        # write lorem's new content to  lorem_file_copy
        write_file(self.lorem_file_copy, lorem_copy_content)
        time.sleep(1)
        ## check if the lorem_file_copy's info is updated in silo
        silo = ComboxSilo(self.config, self.silo_lock)
        assert lorem_file_copy_hash != silo.db.get(self.lorem_file_copy)


        # decrypt_and_glue will decrypt the file shards, glues them and
        # writes it to the respective file
        decrypt_and_glue(self.lorem_file_copy, self.config)
        time.sleep(1)

        lorem_content_from_disk = read_file(self.lorem_file_copy)
        assert lorem_copy_content == lorem_content_from_disk

        # remove lorem_file_copy and confirm that its shards are deleted
        # in the node directories.
        remove(self.lorem_file_copy)
        time.sleep(1)
        path_deletedp(self.lorem_file_copy)
        ## check if the lorem_file_copy's info is deleted from silo
        silo = ComboxSilo(self.config, self.silo_lock)
        assert not silo.exists(self.lorem_file_copy)

        observer.stop()
        observer.join()


    def test_CDM_housekeep(self):
        """ComboxDirMonitor's housekeep method test."""

        # test file deletion and addition
        os.rename(self.lorem, self.lorem_moved)

        cdm = ComboxDirMonitor(self.config, self.silo_lock)
        cdm.housekeep()

        silo = ComboxSilo(self.config, self.silo_lock)
        assert not silo.exists(self.lorem)
        assert silo.exists(self.lorem_moved)
        shardedp(self.lorem_moved)

        ##1
        os.rename(self.lorem_moved, self.lorem)
        rm_shards(self.lorem_moved, self.config)
        silo.remove(self.lorem_moved)

        # test file modification
        copyfile(self.lorem, self.lorem_ipsum)
        assert path.exists(self.lorem_ipsum)

        cdm = ComboxDirMonitor(self.config, self.silo_lock)
        cdm.housekeep()

        silo = ComboxSilo(self.config, self.silo_lock)
        assert silo.exists(self.lorem_ipsum)

        ipsum_content = read_file(self.ipsum)

        lorem_ipsum_content = read_file(self.lorem_ipsum)
        lorem_ipsum_content = "%s\n%s" % (lorem_ipsum_content, ipsum_content)
        write_file(self.lorem_ipsum, lorem_ipsum_content)

        cdm.housekeep()

        silo = ComboxSilo(self.config, self.silo_lock)
        assert not silo.stale(self.lorem_ipsum)


    def test_NDM_numnodes(self):
        """Tests whether the NodeDirMonitor's num_nodes variable has the
        right value.

        """
        nmonitor = NodeDirMonitor(self.config, self.silo_lock,
                                  self.nodem_lock)
        assert_equal(2, nmonitor.num_nodes)


    def test_NDM_oncreated(self):
        """Testing on_created method in NodeDirMonitor"""
        nodes =  get_nodedirs(self.config)
        num_nodes =  len(get_nodedirs(self.config))

        nmonitors = []
        observers = []

        # create an observer for each node directory and make it
        # monitor them.
        for node in nodes:
            nmonitor = NodeDirMonitor(self.config, self.silo_lock,
                                      self.nodem_lock)
            observer = Observer()
            observer.schedule(nmonitor, node, recursive=True)
            observer.start()

            nmonitors.append(nmonitor)
            observers.append(observer)

        # Test - new file addition, when shard is created in node_dirs
        self.TEST_FILE_MUTANT = "%s.mutant" % self.TEST_FILE

        fmutant_content = read_file(self.TEST_FILE)

        split_and_encrypt(self.TEST_FILE_MUTANT, self.config,
                          fmutant_content)
        ## wait for NodeDirMonitor to reconstruct the shards and put
        ## it in combox directory
        time.sleep(1)
        assert fmutant_content == read_file(self.TEST_FILE_MUTANT)
        ## check if the new file's info is in silo
        assert self.silo.exists(self.TEST_FILE_MUTANT)
        assert_equal(None, self.silo.node_get('file_created',
                                              self.TEST_FILE_MUTANT))

        self.purge_list.append(self.TEST_FILE_MUTANT)

        # Test - directory creation
        self.FOO_DIR = path.join(self.FILES_DIR, 'foo')
        mk_nodedir(self.FOO_DIR, self.config)
        time.sleep(1)
        ## check if FOO_DIR is created under the combox directory
        assert path.isdir(self.FOO_DIR)
        assert_equal(None, self.silo.node_get('file_created',
                                              self.FOO_DIR))
        self.BAR_DIR = path.join(self.FOO_DIR, 'bar')
        mk_nodedir(self.BAR_DIR, self.config)
        time.sleep(1)
        ## check if BAR_DIR is created under the combox directory.
        assert path.isdir(self.BAR_DIR)
        assert_equal(None, self.silo.node_get('file_created',
                                              self.BAR_DIR))

        self.purge_list.append(self.FOO_DIR)

        # stop the zarking observers.
        for i in range(num_nodes):
            observers[i].stop()
            observers[i].join()


    def test_NDM_onmodified(self):
        """Testing on_modified method in NodeDirMonitor"""
        nodes =  get_nodedirs(self.config)
        num_nodes =  len(get_nodedirs(self.config))

        nmonitors = []
        observers = []

        # create an observer for each node directory and make it
        # monitor them.
        for node in nodes:
            nmonitor = NodeDirMonitor(self.config, self.silo_lock,
                                      self.nodem_lock)
            observer = Observer()
            observer.schedule(nmonitor, node, recursive=True)
            observer.start()

            nmonitors.append(nmonitor)
            observers.append(observer)

        # Test - shard modification
        self.lorem_file = path.join(self.FILES_DIR, 'lorem.txt')
        lorem_content = read_file(self.lorem_file)
        self.lorem_file_copy = "%s.copy" % self.lorem_file

        copyfile(self.lorem_file, self.lorem_file_copy)
        split_and_encrypt(self.lorem_file_copy, self.config,
                          lorem_content)

        self.silo.update(self.lorem_file_copy)
        shardedp(self.lorem_file_copy)

        self.silo.reload()
        lorem_file_copy_hash = self.silo.db.get(self.lorem_file_copy)

        self.ipsum_file = path.join(self.FILES_DIR, 'ipsum.txt')
        ipsum_content = read_file(self.ipsum_file)
        lorem_copy_content = "%s\n%s" % (lorem_content, ipsum_content)

        split_and_encrypt(self.lorem_file_copy, self.config,
                          lorem_copy_content)
        time.sleep(1)
        assert lorem_copy_content == read_file(self.lorem_file_copy)

        ## check if the lorem_file_copy's info is updated in silo
        self.silo.reload()
        assert lorem_file_copy_hash != self.silo.db.get(self.lorem_file_copy)
        assert_equal(None, self.silo.node_get('file_modified',
                                              self.lorem_file_copy))

        self.purge_list.append(self.lorem_file_copy)

        # stop the zarking observers.
        for i in range(num_nodes):
            observers[i].stop()
            observers[i].join()


    def untest_NDM(self):
        """
        Tests the NodeDirMonitor class.
        """

        event_handler = NodeDirMonitor(self.config, self.silo_lock,
                                       self.nodem_lock)
        observer = Observer()
        observer.schedule(event_handler, self.NODE_DIR, recursive=True)
        observer.start()

        ####
        # Test - new file addition, when shard is created in node_dirs
        self.TEST_FILE_MUTANT = "%s.mutant" % self.TEST_FILE

        fmutant_content = read_file(self.TEST_FILE)

        split_and_encrypt(self.TEST_FILE_MUTANT, self.config,
                          fmutant_content)
        ## wait for NodeDirMonitor to reconstruct the shards and put
        ## it in combox directory
        time.sleep(1)
        assert fmutant_content == read_file(self.TEST_FILE_MUTANT)
        ## check if the new file's info is in silo
        silo = ComboxSilo(self.config, self.silo_lock)
        assert silo.exists(self.TEST_FILE_MUTANT)
        ####

        # Test - Shard deletion.
        rm_shards(self.TEST_FILE_MUTANT, self.config)
        time.sleep(1)
        assert not path.exists(self.TEST_FILE_MUTANT)

        ## check if the new file's info is removed from silo
        silo = ComboxSilo(self.config, self.silo_lock)
        assert not silo.exists(self.TEST_FILE_MUTANT)

        # Test - directory deletion inside node directory
        rm_nodedir(self.BAR_DIR, self.config)
        time.sleep(1)
        assert not path.exists(self.BAR_DIR)

        # Test - shard modification
        self.lorem_file = path.join(self.FILES_DIR, 'lorem.txt')
        lorem_content = read_file(self.lorem_file)
        self.lorem_file_copy = "%s.copy" % self.lorem_file

        copyfile(self.lorem_file, self.lorem_file_copy)
        split_and_encrypt(self.lorem_file_copy, self.config,
                          lorem_content)

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.update(self.lorem_file_copy)
        shardedp(self.lorem_file_copy)

        silo = ComboxSilo(self.config, self.silo_lock)
        lorem_file_copy_hash = silo.db.get(self.lorem_file_copy)

        self.ipsum_file = path.join(self.FILES_DIR, 'ipsum.txt')
        ipsum_content = read_file(self.ipsum_file)
        lorem_copy_content = "%s\n%s" % (lorem_content, ipsum_content)

        split_and_encrypt(self.lorem_file_copy, self.config,
                          lorem_copy_content)
        time.sleep(1)
        ## check if the lorem_file_copy's info is updated in silo
        silo = ComboxSilo(self.config, self.silo_lock)

        assert lorem_copy_content == read_file(self.lorem_file_copy)
        assert lorem_file_copy_hash != silo.db.get(self.lorem_file_copy)

        self.purge_list.append(self.lorem_file_copy)

        observer.stop()
        observer.join()


    def test_NDM_onmoved(self):
        """Testing on_moved method in NodeDirMonitor"""

        event_handler = NodeDirMonitor(self.config, self.silo_lock,
                                       self.nodem_lock)
        observer = Observer()
        observer.schedule(event_handler, self.NODE_DIR, recursive=True)
        observer.start()

        self.testf = "%s.onm" % self.TEST_FILE
        copyfile(self.TEST_FILE, self.testf)

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.update(self.testf)

        split_and_encrypt(self.testf, self.config)
        time.sleep(1)

        self.testf_moved = "%s.onm.moved" % self.TEST_FILE

        # test file move/rename
        move_shards(self.testf, self.testf_moved, self.config)
        time.sleep(1)
        assert path.isfile(self.testf_moved)

        silo = ComboxSilo(self.config, self.silo_lock)
        assert silo.exists(self.testf_moved)

        # test directory move/rename
        dirt = path.join(self.FILES_DIR, "fom")
        os.mkdir(dirt)
        mk_nodedir(dirt, self.config)

        dirt_lorem = path.join(dirt, "lorem.txt")
        copyfile(self.lorem, dirt_lorem)
        split_and_encrypt(dirt_lorem, self.config)
        time.sleep(1)

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.update(dirt_lorem)

        dirt_m = path.join(self.FILES_DIR, "mof")
        dirt_m_lorem = path.join(dirt_m, "lorem.txt")
        move_nodedir(dirt, dirt_m, self.config)
        time.sleep(1)

        assert path.isdir(dirt_m)
        assert path.isfile(dirt_m_lorem)

        silo = ComboxSilo(self.config, self.silo_lock)
        assert silo.exists(dirt_m_lorem)

        self.purge_list.append(self.testf_moved)
        self.purge_list.append(dirt_m)

        observer.stop()
        observer.join()


    def test_NDM_housekeep(self):
        """Testing NodeDirMonitor's housekeep method."""

        # files for testing deletion.
        testf1 = path.join(self.FILES_DIR, 'hitchhikers.png')
        testf2 = path.join(self.FILES_DIR, 'lorem.housekeep')
        copyfile(self.TEST_FILE, testf1)
        copyfile(self.lorem, testf2)

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.update(testf1)
        silo.update(testf2)

        ndm = NodeDirMonitor(self.config, self.silo_lock,
                             self.nodem_lock)
        ndm.housekeep()

        assert not path.exists(testf1)
        assert not path.exists(testf2)

        self.purge_list.append(testf1)
        self.purge_list.append(testf2)

        # test shard creation
        hmutant = "%s.mutant" % self.TEST_FILE
        hmutant_content = read_file(self.TEST_FILE)

        split_and_encrypt(hmutant, self.config,
                          hmutant_content)

        ndm = NodeDirMonitor(self.config, self.silo_lock,
                             self.nodem_lock)
        ndm.housekeep()

        assert path.exists(hmutant)
        assert hmutant_content == read_file(hmutant)

        self.purge_list.append(hmutant)

        # test shard modification
        lcopy = "%s.copy" % self.lorem
        copyfile(self.lorem, lcopy)
        lcopy_content = read_file(lcopy)
        split_and_encrypt(lcopy, self.config,
                          lcopy_content)

        silo = ComboxSilo(self.config, self.silo_lock)
        silo.update(lcopy)
        shardedp(lcopy)

        silo = ComboxSilo(self.config, self.silo_lock)
        lcopy_hash = silo.db.get(lcopy)

        ipsum_content = read_file(self.ipsum)
        lcopy_content = "%s\n%s" % (lcopy_content, ipsum_content)

        split_and_encrypt(lcopy, self.config,
                          lcopy_content)

        ndm = NodeDirMonitor(self.config, self.silo_lock,
                             self.nodem_lock)
        ndm.housekeep()

        ## check if the lorem_file_copy's info is updated in silo
        silo = ComboxSilo(self.config, self.silo_lock)

        assert lcopy_content == read_file(lcopy)
        assert hash_file(lcopy, lcopy_content) == silo.db.get(lcopy)

        self.purge_list.append(lcopy)


    def test_NDM_shardp(self):
        """Testing shardp method in NodeDirMonitor class"""
        shard = 'some.shard0'
        not_shard = 'some.extension'
        ndm = NodeDirMonitor(self.config, self.silo_lock,
                             self.nodem_lock)

        assert_equal(True, ndm.shardp(shard))
        assert_equal(False, ndm.shardp(not_shard))


    def teardown(self):
        """Cleans up things after each test in this class"""

        purge_nodedirs(self.config)
        self.silo.db.deldb()
        purge(self.purge_list)


    @classmethod
    def teardown_class(self):
        """Purge the mess created by this test"""

        rm_shards(self.TEST_FILE, self.config)

        os.remove(self.lorem_ipsum)
        rm_shards(self.lorem_ipsum, self.config)

        rm_shards(self.lorem, self.config)

        rm_shards(self.ipsum, self.config)

        rm_nodedirs(self.config)
        rm_configdir()
