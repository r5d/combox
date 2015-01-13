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

from glob import glob
from nose.tools import *
from os import path, remove

from combox.file import (split_data, glue_data, write_file,
                  read_file, write_shards, read_shards)

CONFIG_DIR = path.join('tests', 'test-config')

config_file = path.join(CONFIG_DIR, 'config.yaml')
try:
    config = yaml.load(file(config_file, 'r'))
except yaml.YAMLError, exc:
    raise AssertionError("Error in configuration file:", exc)


FILES_DIR = config['combox_dir']
TEST_FILE = path.join(FILES_DIR,'the-red-star.jpg')

def test_split():
    """Test to split, glue and create a copy of the image file from the
    glued image file.

    """

    f = path.abspath(TEST_FILE)
    f_content = read_file(f)
    f_parts = split_data(f_content, 5)
    f_content_glued = glue_data(f_parts)

    assert f_content == f_content_glued
    #f_copy = path.abspath('tests/files/the-red-star-copy.jpg')
    #write_file(f_copy, f_content)


def test_shards():
    """Split file into N shards, write them to disk, glue them together
and check if they're the same as the orginal file.
    """

    # no. of shards = no. of nodes
    SHARDS = len(config['nodes_info'].keys())

    f = path.abspath(TEST_FILE)
    f_content = read_file(f)
    f_shards = split_data(f_content, SHARDS)

    f_basename = path.basename(f)
    nodes = [path.abspath(node['path']) for node in config['nodes_info'].itervalues()]
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
