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

## Adapted from https://gist.github.com/sekondus/4322469

import base64
import os

from combox.config import get_nodedirs
from combox.file import (read_file, write_file,
                         read_shards, write_shards,
                         split_data, glue_data,
                         relative_path)
from combox.log import log_i

from Crypto.Cipher import AES
from datetime import datetime
from os import path

BLOCK_SIZE = 32
"""Specifies the block size of the data that is given to crypto functions.

"""

PAD_CHAR = '#'
"""Character for padding data to make it a multiple of :data:`BLOCK_SIZE`.

"""

def pad(data):
    """Pad `data` such that its length is a multiple of :data:`BLOCK_SIZE`.

    :param str data:
        A string that needs to be padded so that its total length is a
        multiple of :data:`BLOCK_SIZE`.
    :returns:
        Padded data whose length is a multiple of :data:`BLOCK_SIZE`.
    :rtype: str

    """
    padding = (BLOCK_SIZE - (len(data) % BLOCK_SIZE)) * PAD_CHAR
    data += padding

    return data


def encrypt(data, secret):
    """Encrypt `data` and return cipher.

    :param str data:
        Data to encrypt.
    :param str secret:
        The key to encrypt the `data` with.
    :returns:
       Encrypted `data` as :mod:`base64` encoded string.
    :rtype: str

    """
    aes = AES.new(pad(secret))
    cipher = base64.b64encode(aes.encrypt(pad(data)))

    return cipher


def decrypt(cipher, secret):
    """Decrypt `cipher` and return data.

    :param str cipher:
        Encrypted data to decrypt.
    :param str secret:
        The key to decrypt the `cipher` with.
    :returns:
        Decrypted data.
    :rtype: str

    """
    aes = AES.new(pad(secret))
    data = aes.decrypt(base64.b64decode(cipher)).rstrip(PAD_CHAR)

    return data


def encrypt_shards(shards, secret):
    """Encrypt the `shards` of data and return a list of ciphers.

    :param list shards:
        List of shards (strings).
    :param str secret:
        The key to encrypt each shard.
    :returns:
        List containing the encrypted shards.
    :rtype: list

    """
    ciphers = []
    for shard in shards:
        cipher = encrypt(shard, secret)
        ciphers.append(cipher)

    return ciphers


def decrypt_shards(ciphers, secret):
    """Decrypt the ciphered shards and return a list of shards.

    :param list ciphers:
        List of encrypted shards (strings).
    :param str secret:
        The key to decrypt each shard.
    :returns:
        List containing the decrypted shards.
    :rtype: list

    """
    shards = []
    for cipher in ciphers:
        shard = decrypt(cipher, secret)
        shards.append(shard)

    return shards


def split_and_encrypt(fpath, config, fcontent=None):
    """Splits file `fpath` into shards, encrypts the shards and spreads the shards across the node directories.

    Information about the node directories must be contained with the
    `config` dictionary; structure of the `config` dict::

             {
              'combox_dir': '/home/rsd/combox/',
              'nodes_info': {
                  'node-1': {
                     'available': '1024',
                     'path': '/home/rsd/combox-nodes/Dropbox',
                     'size': '1024'
                  },
                  'node-0': {
                     'available': '1024',
                     'path': '/home/rsd/combox-nodes/Googl-Drive/',
                     'size': '1024'
                  }
              },
              'silo_dir': '/home/rsd/bgc/combox/tests/test-config',
              'topsecret': 'topsecret',
              'combox_name': 'testbox'
             }

    :param str fpath:
        Path to an existent file.
    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :param str fcontent:
        Contents of the file at `fpath` (optional). When `None`, the
        content of the file is read from disk; otherwise it just
        assumes `fcontent` is the content of the file.

    """
    start = datetime.now()

    rel_path = relative_path(fpath, config)

    # no. of shards = no. of nodes.
    SHARDS = len(config['nodes_info'].keys())

    f = path.join(config['combox_dir'], rel_path)

    if not fcontent:
        fcontent = read_file(f)

    f_shards = split_data(fcontent, SHARDS)

    # encrypt shards
    ciphered_shards = encrypt_shards(f_shards, config['topsecret'])


    # write ciphered shards to disk
    f_basename =  rel_path
    # gets the list of node' directories.
    nodes = get_nodedirs(config)

    write_shards(ciphered_shards, nodes, f_basename)

    end = datetime.now()
    duration = (end - start).total_seconds() * pow(10, 3)
    log_i('Took %f ms  to split and encrypt %s' % (duration, fpath))


def decrypt_and_glue(fpath, config, write=True):
    """Reads encrypted shards from the node directories, decrypts and reconstructs `fpath`.

    :param str fpath:
        The path to a file under the combox directory that has to be
        decrypted and glued from the node directories.
    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :param bool write:
        If `True`, writes the reconstructed content to disk.
    :returns:
        The glued content.
    :rtype: str

    """
    rel_path = relative_path(fpath, config)

    f = path.abspath(fpath)
    f_basename = rel_path
    # gets the list of node' directories.
    nodes = get_nodedirs(config)

    ciphered_shards = read_shards(nodes, f_basename)

    # decrypt shards
    f_parts = decrypt_shards(ciphered_shards, config['topsecret'])

    # glue them together
    f_content = glue_data(f_parts)

    if write:
        # write the glued content to fpath
        write_file(f, f_content)

    return f_content
