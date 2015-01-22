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
from combox.file import read_file, write_file

CONFIG_DIR = path.join('tests', 'test-config')

config_file = path.join(CONFIG_DIR, 'config.yaml')
try:
    config = yaml.load(file(config_file, 'r'))
except yaml.YAMLError, exc:
    raise AssertionError("Error in configuration file:", exc)


FILES_DIR = path.abspath(config['combox_dir'])
LOREM = path.join(FILES_DIR,'lorem.txt')
LOREM_IPSUM = path.join(FILES_DIR,'lorem-ipsum.txt')
IPSUM = path.join(FILES_DIR,'ipsum.txt')


def test_csilo():
    """
    Tests the ComboxSilo class.
    """
    csilo = ComboxSilo(config)


    # Test - update
    csilo.update(LOREM)
    lorem_content = read_file(LOREM)
    lorem_hash = csilo.db.get(LOREM)
    assert lorem_hash

    csilo.update(IPSUM)
    ispum_content = read_file(IPSUM)
    ipsum_hash = csilo.db.get(IPSUM)
    assert ipsum_hash

    lorem_ipsum_content = "%s\n%s" % (LOREM, IPSUM)
    write_file(LOREM_IPSUM, lorem_ipsum_content)

    csilo.update(LOREM_IPSUM)
    lorem_ipsum_hash = csilo.db.get(LOREM_IPSUM)
    assert lorem_ipsum_hash

    assert lorem_ipsum_hash != lorem_hash
    assert lorem_ipsum_hash != ipsum_hash

    # Test - stale
    lorem_ipsum_content = "%s\n%s" % (lorem_ipsum_content, IPSUM)
    write_file(LOREM_IPSUM, lorem_ipsum_content)

    assert csilo.stale(LOREM_IPSUM)
    csilo.update(LOREM_IPSUM)
    assert csilo.stale(LOREM_IPSUM) is False

    lorem_ipsum_hash_new = csilo.db.get(LOREM_IPSUM)
    assert lorem_ipsum_hash_new
    assert lorem_ipsum_hash_new != lorem_ipsum_hash

    # Test - remove
    remove(LOREM_IPSUM)
    csilo.remove(LOREM_IPSUM)

    # Test - exists
    assert not csilo.exists(LOREM_IPSUM)
