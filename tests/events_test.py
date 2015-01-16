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

import os
import yaml

from filecmp import cmp
from glob import glob
import time
from nose.tools import *
from os import path, remove
from shutil import copyfile
from watchdog.observers import Observer

from combox.events import ComboxEventHandler
from combox.config import get_nodedirs
from combox.file import relative_path, purge_dir

CONFIG_DIR = path.join('tests', 'test-config')

config_file = path.join(CONFIG_DIR, 'config.yaml')
try:
    config = yaml.load(file(config_file, 'r'))
except yaml.YAMLError, exc:
    raise AssertionError("Error in configuration file:", exc)

FILES_DIR = path.abspath(config['combox_dir'])
TEST_FILE = path.join(FILES_DIR,'thgttg-21st.png')


def shardedp(f):
    """Checks if file's shards exists in the node directories"""

    nodes = get_nodedirs(config)
    i = 0
    for node in nodes:
        rel_path = relative_path(f, config)
        shard = "%s.shard%s" % (path.join(node, rel_path), i)
        i += 1
        assert path.isfile(shard)

def dirp(d):
    """
    Checks if the directory was created under node directories
    """

    nodes = get_nodedirs(config)
    for node in nodes:
        rel_path = relative_path(d, config)
        directory = path.join(node, rel_path)
        assert path.isdir(directory)


def path_deletedp(p):
    """
    Checks if the directory or respective file shards  is deleted under node directories.

    p: path to the directory or file, under the combox directory, that was deleted.
    """

    nodes = get_nodedirs(config)

    is_dir = True if path.isdir(p) else False
    i = 0

    for node in nodes:
        rel_path = relative_path(p, config)

        if is_dir:
            path_ = path.join(node, rel_path)
        else:
            path_ = "%s.shard%s" % (path.join(node, rel_path), i)
            i += 1

        assert not path.exists(path_)


def test_CEH():
    """
    Tests the ComboxEventHandler class.
    """

    event_handler = ComboxEventHandler(config)
    observer = Observer()
    observer.schedule(event_handler, FILES_DIR, recursive=True)
    observer.start()

    # Test - new file addition
    TEST_FILE_COPY_0 = "%s.mutant" % TEST_FILE
    copyfile(TEST_FILE, TEST_FILE_COPY_0)
    ## wait for ComboxEventHandler to split and scatter the file in the
    ## node directories.
    time.sleep(1)
    ## check if the shards were created.
    shardedp(TEST_FILE_COPY_0)

    # Test - File deletion.
    remove(TEST_FILE_COPY_0)
    time.sleep(1)
    path_deletedp(TEST_FILE_COPY_0)

    # Test - directory creation
    TEST_DIR_0 = path.join(FILES_DIR, 'foo')
    os.mkdir(TEST_DIR_0)
    time.sleep(2)
    ## check if TEST_DIR_0 is created under node directories.
    dirp(TEST_DIR_0)

    TEST_DIR_1 = path.join(TEST_DIR_0, 'bar')
    os.mkdir(TEST_DIR_1)
    time.sleep(2)
    ## check if TEST_DIR_1 is created under node directories.
    dirp(TEST_DIR_1)

    # Test - new file in a nested directory
    TEST_FILE_COPY_1 = path.join(TEST_DIR_1, path.basename(TEST_FILE))
    copyfile(TEST_FILE, TEST_FILE_COPY_1)
    time.sleep(1)
    shardedp(TEST_FILE_COPY_1)

    # Test directory & file deletion
    purge_dir(TEST_DIR_0)
    # remove the directory itself.
    os.rmdir(TEST_DIR_0)
    time.sleep(2)
    path_deletedp(TEST_FILE_COPY_1)
    path_deletedp(TEST_DIR_1)
    path_deletedp(TEST_DIR_0)

    observer.stop()
    observer.join()
