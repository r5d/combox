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
from combox.crypto import decrypt_and_glue
from combox.file import (relative_path, purge_dir,
                         read_file, write_file)

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

def renamedp(old_p, new_p):
    """
    Checks if the file shards or directory were/was renamed in the  under the node directories.

    old_p: old path to directory or file under combox directory.
    new_p: new (present) path to the directory or file under combox directory.
    """

    nodes = get_nodedirs(config)

    is_dir = True if path.isdir(new_p) else False
    i = 0

    for node in nodes:
        old_rel_path = relative_path(old_p, config)
        new_rel_path = relative_path(new_p, config)

        if is_dir:
            old_path = path.join(node, old_rel_path)
            new_path = path.join(node, new_rel_path)
        else:
            old_path = "%s.shard%s" % (path.join(node, old_rel_path), i)
            new_path = "%s.shard%s" % (path.join(node, new_rel_path), i)
            i += 1

        assert not path.exists(old_path)
        assert path.exists(new_path)


def path_deletedp(p, is_dir=False):
    """
    Checks if the directory or respective file shards  is deleted under node directories.

    p: path to the directory or file, under the combox directory, that was deleted.
    is_dir: set to True if `p' denotes a deleted directory. Default value is False.
    """

    nodes = get_nodedirs(config)

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

    # Test - dir rename
    TEST_DIR_1_NEW = path.join(path.dirname(TEST_DIR_1),
                               'snafu')
    TEST_FILE_COPY_1_NEW = path.join(TEST_DIR_1_NEW, path.basename(TEST_FILE))
    os.rename(TEST_DIR_1, TEST_DIR_1_NEW)
    time.sleep(1)
    renamedp(TEST_DIR_1, TEST_DIR_1_NEW)
    renamedp(TEST_FILE_COPY_1, TEST_FILE_COPY_1_NEW)

    # Test directory & file deletion
    purge_dir(TEST_DIR_0)
    # remove the directory itself.
    os.rmdir(TEST_DIR_0)
    time.sleep(2)
    path_deletedp(TEST_FILE_COPY_1)
    path_deletedp(TEST_DIR_1, True)
    path_deletedp(TEST_DIR_0, True)


    # Test - file modification
    lorem_file = path.join(FILES_DIR, 'lorem.txt')
    lorem_file_copy = "%s.copy" % lorem_file
    # this will shard lorem.txt.copy in the node directories.
    copyfile(lorem_file, lorem_file_copy)
    time.sleep(1)
    shardedp(lorem_file_copy)

    ipsum_file = path.join(FILES_DIR, 'ipsum.txt')
    ipsum_content = read_file(ipsum_file)
    lorem_content = read_file(lorem_file_copy)
    lorem_content = "%s\n%s" % (lorem_content, ipsum_content)

    # write lorem's new content to  lorem_file_copy
    write_file(lorem_file_copy, lorem_content)
    time.sleep(1)

    # decrypt_and_glue will decrypt the file shards, glues them and
    # writes it to the respective file
    decrypt_and_glue(lorem_file_copy, config)
    time.sleep(1)

    lorem_content_from_disk = read_file(lorem_file_copy)
    assert lorem_content == lorem_content_from_disk

    # remove lorem_file_copy and confirm that its shards are deleted
    # in the node directories.
    remove(lorem_file_copy)
    time.sleep(1)
    path_deletedp(lorem_file_copy)

    observer.stop()
    observer.join()
