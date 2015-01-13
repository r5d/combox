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
from combox.crypto import encrypt, decrypt, encrypt_shards, decrypt_shards


FILES_DIR = path.join('tests','files')
TEST_FILE = path.join(FILES_DIR,'the-red-star.jpg')
PASS = 'topsecret'

def test_encryption():
    """ Read file, encrypt it to a cipher, write cipher to file, read
    encrypted file, decrypt it, write decrypted data to file.
"""

    f = path.abspath(TEST_FILE)
    f_content = read_file(f)

    # encrypt
    f_cipher = encrypt(f_content, PASS)
    # decrypt
    f_content_decrypted = decrypt(f_cipher, PASS)

    assert f_content == f_content_decrypted


def test_split_encryption():
    """Read file, split it, encrypt shards, write encrypted shards to
    file, read encrypted shards from file, decrypt the encrypted shards,
    glue the shards together, write glued data to file.
    """

    f = path.abspath(TEST_FILE)
    f_content = read_file(f)
    f_shards = split_data(f_content, 5)

    # encrypt shards
    ciphered_shards = encrypt_shards(f_shards, PASS)

    # write ciphered shards to disk
    f_path = FILES_DIR
    f_basename = "%s.ciphered" % path.basename(f)
    write_shards(ciphered_shards, f_path, f_basename)

    # read ciphered shards from disk
    ciphered_shards = read_shards(f_path, f_basename)

    # decrypt shards
    f_parts = decrypt_shards(ciphered_shards, PASS)
    # glue them shards together
    f_content_glued = glue_data(f_parts)

    assert f_content == f_content_glued

    # remove ciphered shards from disk
    c_shards = glob("%s.ciphered*" % TEST_FILE)
    for shard in c_shards:
        remove(shard)
