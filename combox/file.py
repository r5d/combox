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
from sys import exit
from glob import glob


def split_data(data, n):
    """Split data into `n' parts and return them as an array.

    data: Stream of bytes or string
    n: Number of parts the file has to be split.
    """

    d_parts = []
    # File size in bytes.
    data_size = len(data)
    # No. of bytes for each data part.
    part_size =  data_size / n
    # Take note of remaining bytes; this is non-zero when data_size is
    # not divisible by `n'.
    rem_bytes = data_size % n

    start = 0
    end = part_size
    while end <= data_size:
        d_parts.append(data[start:end])
        start = end
        end = end + part_size

    # read the remaining bytes into the last data part.
    end += start + rem_bytes
    d_parts[n-1] += data[start:end]

    return d_parts


def glue_data(d_parts):
    """Glue different parts of the data to one.

    d_parts: Array containing different parts of the data. Each part
    is a sequence of bytes.
    """

    data = ''
    for part in d_parts:
        data += part

    return data


def read_file(filename):
    """Read file and return it as a string.

    filename: Absolute pathname of the file.
    """
    file_ = None
    try:
      file_   = open(filename, 'rb')
    except IOError:
        print "ERROR: opening %s" % (filename)
        exit(1)

    return file_.read()


def write_file(filename, filecontent):
    """Write `filecontent' to `filename'.

    filename: Absolute pathname of the file.
    filecontent: String/bytstream to write to filename.
    """
    file_ = None
    try:
      file_   = open(filename, 'wb')
      file_.write(filecontent)
    except IOError:
        print "ERROR: creating and writing content to %s" % (filename)
        exit(1)

def write_shards(shards, directories, shard_basename):
    """Write shards to respective files respective files.

    shard: list of strings (ciphers or data).
    directories: absolute path of directories to which it shards must be written to.
    shard_basename: base name of the shard.
    """

    shard_no = 0
    for directory in directories:
        # partial filename of the shard
        p_filename =  path.join(directory, shard_basename)
        shard_name =  "%s.shard%s" % (p_filename, shard_no)
        write_file(shard_name, shards[shard_no])
        shard_no += 1

def read_shards(directories, shard_basename):
    """Read the shards from directory and return it as a list.

    directories: absolute path of directories from which to read the shards.
    shard_basename: base name of the shard.
    """

    # get the names of the file shards
    file_shards = []
    for directory in directories:
        filename_glob = "%s.shard*" % path.join(directory, shard_basename)
        file_shard = glob(filename_glob)[0]
        file_shards.append(file_shard)

    shards = []
    for file_shard in sorted(file_shards):
        shard_content = read_file(file_shard)
        shards.append(shard_content)

    return shards
