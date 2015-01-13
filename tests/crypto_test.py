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

from combox.file import *
from combox.crypto import *


CONFIG_DIR = path.join('tests', 'test-config')

config_file = path.join(CONFIG_DIR, 'config.yaml')
try:
    config = yaml.load(file(config_file, 'r'))
except yaml.YAMLError, exc:
    raise AssertionError("Error in configuration file:", exc)

FILES_DIR = config['combox_dir']
TEST_FILE = path.join(FILES_DIR,'the-red-star.jpg')


def test_encryption():
    """ Read file, encrypt it to a cipher, write cipher to file, read
    encrypted file, decrypt it, write decrypted data to file.
"""

    f = path.abspath(TEST_FILE)
    f_content = read_file(f)

    # encrypt
    f_cipher = encrypt(f_content, config['topsecret'])
    # decrypt
    f_content_decrypted = decrypt(f_cipher, config['topsecret'])

    assert f_content == f_content_decrypted


def test_split_encryption():
    """Read file, split it, encrypt shards, write encrypted shards to
    file, read encrypted shards from file, decrypt the encrypted shards,
    glue the shards together, write glued data to file.
    """

    # no. of shards = no. of nodes
    SHARDS = len(config['nodes_info'].keys())

    f = path.abspath(TEST_FILE)
    f_content = read_file(f)
    f_shards = split_data(f_content, SHARDS)

    # encrypt shards
    ciphered_shards = encrypt_shards(f_shards, config['topsecret'])

    # write ciphered shards to disk
    f_basename = "%s.ciphered" % path.basename(f)
    nodes = [path.abspath(node['path']) for node in config['nodes_info'].itervalues()]
    write_shards(ciphered_shards, nodes, f_basename)

    # read ciphered shards from disk
    ciphered_shards = read_shards(nodes, f_basename)

    # decrypt shards
    f_parts = decrypt_shards(ciphered_shards, config['topsecret'])
    # glue them shards together
    f_content_glued = glue_data(f_parts)

    assert f_content == f_content_glued
