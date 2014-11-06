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

from os import path

from file import (split_data, glue_data, write_file,
                  read_file, write_shards, read_shards)
from crypto import encrypt, decrypt, encrypt_shards, decrypt_shards

PASS = 'topsecret'
### Read file, encrypt it to a cipher, write cipher to file, read
### encrypted file, decrypt it, write decrypted data to file.
f = path.abspath('tests/files/the-red-star.jpg')
f_content = read_file(f)
f_cipher = encrypt(f_content, PASS)
f_encrypted = path.abspath('tests/files/the-red-star.cipher')
write_file(f_encrypted, f_cipher)
f_cipher = read_file(f_encrypted)
f_content = decrypt(f_cipher, PASS)
f = path.abspath('tests/files/the-red-star-decrypted.jpg')
write_file(f, f_content)

### Read file, split it, encrypt shards, write encrypted shards to
### file, read encrypted shards from file, decrypt the encrypted
### shards, glue the shards together, write glued data to file.
f = path.abspath('tests/files/the-red-star.jpg')
f_content = read_file(f)
f_shards = split_data(f_content, 5)
ciphered_shards = encrypt_shards(f_shards, PASS)
f_path = path.dirname(f)
f_basename = "%s.ciphered" % path.basename(f)
write_shards(ciphered_shards, f_path, f_basename)
ciphered_shards = read_shards(f_path, f_basename)
f_parts = decrypt_shards(ciphered_shards, PASS)
f_content = glue_data(f_parts)
f = path.abspath('tests/files/the-red-star-from-ciphered-shards.jpg')
write_file(f, f_content)
