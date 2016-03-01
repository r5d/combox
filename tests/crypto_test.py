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

from filecmp import cmp
from glob import glob
from nose.tools import *
from os import path, remove
from shutil import copyfile

from combox.config import get_nodedirs
from combox.crypto import *
from combox.file import *
from tests.utils import get_config, rm_nodedirs, rm_configdir


class TestCrypto(object):
    """
    Class that tests the crypto.py module.
    """

    @classmethod
    def setup_class(self):
        """Set things up."""

        self.config = get_config()
        FILES_DIR = self.config['combox_dir']
        self.TEST_FILE = path.join(FILES_DIR,'thgttg-21st.png')

        # create a copy of TEST_FILE (for later comparision)
        self.TEST_FILE_COPY = "%s.copy" % self.TEST_FILE
        copyfile(self.TEST_FILE, self.TEST_FILE_COPY)


    def test_encryption(self):
        """ Read file, encrypt it to a cipher, write cipher to file, read
        encrypted file, decrypt it, write decrypted data to file.
        """

        f = path.abspath(self.TEST_FILE)
        f_content = read_file(f)

        # encrypt
        f_cipher = encrypt(f_content, self.config['topsecret'])
        # decrypt
        f_content_decrypted = decrypt(f_cipher, self.config['topsecret'])

        assert f_content == f_content_decrypted


    def test_split_encryption(self):
        """Read file, split it, encrypt shards, write encrypted shards to
        file, read encrypted shards from file, decrypt the encrypted shards,
        glue the shards together, write glued data to file.
        """

        # no. of shards = no. of nodes
        SHARDS = len(self.config['nodes_info'].keys())

        f = path.abspath(self.TEST_FILE)
        f_content = read_file(f)
        f_shards = split_data(f_content, SHARDS)

        # encrypt shards
        ciphered_shards = encrypt_shards(f_shards, self.config['topsecret'])

        # write ciphered shards to disk
        # f_basename = path.basename(f)
        f_basename = relative_path(f, self.config)
        nodes = get_nodedirs(self.config)
        write_shards(ciphered_shards, nodes, f_basename)

        # read ciphered shards from disk
        ciphered_shards = read_shards(nodes, f_basename)

        # decrypt shards
        f_parts = decrypt_shards(ciphered_shards, self.config['topsecret'])
        # glue them shards together
        f_content_glued = glue_data(f_parts)

        assert f_content == f_content_glued


    def test_convenience_crypto(self):
        """
        Tests convenience crypto function(s) - split_and_encrypt, decrypt and glue.
        """

        # splits file into shards, writes encrypted shards to respective
        # node directories.
        split_and_encrypt(self.TEST_FILE, self.config)

        # reads encrypted shards from node directories, glues them and
        # writes decrypted back to combox directory.
        os.remove(self.TEST_FILE)
        decrypt_and_glue(self.TEST_FILE, self.config, write=False)
        assert not path.exists(self.TEST_FILE)

        decrypt_and_glue(self.TEST_FILE, self.config)
        assert path.exists(self.TEST_FILE)
        assert cmp(self.TEST_FILE, self.TEST_FILE_COPY, False)


    @classmethod
    def teardown_class(self):
        """Purge the mess created by this test"""

        rm_shards(self.TEST_FILE, self.config)
        remove(self.TEST_FILE_COPY)
        rm_nodedirs(self.config)
        rm_configdir()
