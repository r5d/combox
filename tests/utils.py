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

from nose.tools import *
from os import path, remove, rmdir

from combox.config import config_cb, get_nodedirs
from combox.file import relative_path, purge_dir

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
    config_info = ['testbox', combox_dir, '', '2',
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


def rm_nodedirs(config):
    """Purges and removes node directories."""
    nodes = get_nodedirs(config)
    purge_nodedirs(config)

    for node in nodes:
        try:
            rmdir(node)
        except OSError, e:
            print "Problem deleting", node, e


def purge(l):
    """ Purges everything in list `l'"""
    for f in l:
        if path.exists(f) and path.isfile(f):
            remove(f)
        elif path.exists(f) and path.isdir(f):
            purge_dir(f)
            rmdir(f)


def purge_nodedirs(config):
    """Purges everything inside node directories."""
    nodes = get_nodedirs(config)
    for node in nodes:
        purge_dir(node)


def rm_configdir():
    """Removes the combox test config directory."""
    config_dir = path.join('tests', 'test-config')
    try:
        purge_dir(config_dir)
        rmdir(config_dir)
    except OSError, e:
        print "Problem deleting", config_dir, e


def shardedp(f):
    """Checks if file's shards exists in the node directories"""

    config = get_config()
    nodes = get_nodedirs(config)
    i = 0
    for node in nodes:
        rel_path = relative_path(f, config)
        shard = "%s.shard%s" % (path.join(node, rel_path), i)
        i += 1
        assert path.exists(shard) and path.isfile(shard)


def not_shardedp(f):
    """Checks if file's shards does not exists in the node directories"""
    config = get_config()
    nodes = get_nodedirs(config)
    i = 0
    for node in nodes:
        rel_path = relative_path(f, config)
        shard = "%s.shard%s" % (path.join(node, rel_path), i)
        i += 1
        assert not path.exists(shard) and not path.isfile(shard)


def dirp(d):
    """
    Checks if the directory was created under node directories
    """
    config = get_config()
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

    config = get_config()
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

    config = get_config()
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
