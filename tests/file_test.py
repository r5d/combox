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

from glob import glob
from nose.tools import *
from os import path, remove

from combox.file import (split_data, glue_data, write_file,
                  read_file, write_shards, read_shards)

FILES_DIR = path.join('tests','files')
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

    SHARDS = 5
    f = path.abspath(TEST_FILE)
    f_content = read_file(f)
    f_shards = split_data(f_content, SHARDS)
    f_path = FILES_DIR
    f_basename = path.basename(f)
    write_shards(f_shards, f_path, f_basename)

    # check if the shards have been created.
    for i in range(0,SHARDS):
        shard = "%s.shard%s" % (TEST_FILE, i)
        assert path.isfile(shard)


    f_shards = read_shards(f_path, f_basename)
    f_content_glued = glue_data(f_shards)

    assert f_content == f_content_glued

    # remove shards from disk.
    shards = glob("%s.shard*" % TEST_FILE)
    for shard in shards:
        remove(shard)
