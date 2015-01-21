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

## Adapted from https://gist.github.com/sekondus/4322469

import base64
import os

from combox.config import get_nodedirs
from combox.file import (read_file, write_file,
                         read_shards, write_shards,
                         split_data, glue_data,
                         relative_path)

from Crypto.Cipher import AES
from os import path

BLOCK_SIZE = 32
PAD_CHAR = '#'


def pad(data):
    """Pad data such that its length is a multiple of BLOCK_SIZE.
    """

    padding = (BLOCK_SIZE - (len(data) % BLOCK_SIZE)) * PAD_CHAR
    data += padding

    return data


def encrypt(data, secret):
    """Encrypt byestream and return cipher.
    """
    aes = AES.new(pad(secret))
    cipher = base64.b64encode(aes.encrypt(pad(data)))
    
    return cipher


def decrypt(cipher, secret):
    """Decrypt cipher and return data.
    """
    aes = AES.new(pad(secret))
    data = aes.decrypt(base64.b64decode(cipher)).rstrip(PAD_CHAR)

    return data

def encrypt_shards(shards, secret):
    """Encrypt the shards of data and return a list of ciphers.

    shards: list of shards (string, bytes).
    secret: top secret passphrase
    """

    ciphers = []
    for shard in shards:
        cipher = encrypt(shard, secret)
        ciphers.append(cipher)

    return ciphers


def decrypt_shards(ciphers, secret):
    """Decrypt the ciphered shards and return a list of shards.

    shards: list of ciphered shards.
    secret: top secret passphrase
    """

    shards = []
    for cipher in ciphers:
        shard = decrypt(cipher, secret)
        shards.append(shard)

    return shards


def split_and_encrypt(fpath, config):
    """
    Splits the file, encrypts the shards and writes them to the nodes.

    fpath: The path to file that has to be split.
    config: The dictonary containing the combox configuration information.
    """

    rel_path = relative_path(fpath, config)

    # no. of shards = no. of nodes.
    SHARDS = len(config['nodes_info'].keys())

    f = path.join(config['combox_dir'], rel_path)
    f_content = read_file(f)
    f_shards = split_data(f_content, SHARDS)

    # encrypt shards
    ciphered_shards = encrypt_shards(f_shards, config['topsecret'])


    # write ciphered shards to disk
    f_basename =  rel_path
    # gets the list of node' directories.
    nodes = get_nodedirs(config)

    write_shards(ciphered_shards, nodes, f_basename)


def decrypt_and_glue(fpath, config):

    """
    Reads encrypted shards, decrypts and glues them.

    fpath: The path to file that has to be decrypted & glued from the nodes.
    config: The dictonary containing the combox configuration information.

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

    # write the glued content to fpath
    write_file(f, f_content)
