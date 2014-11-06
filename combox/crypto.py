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

## Adapted from https://gist.github.com/sekondus/4322469

import base64
import os

from Crypto.Cipher import AES

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
