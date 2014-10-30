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


def split_file(filename, n):
    """Split the file into `n' parts and return them as an array.

    filename: Absolute pathname of the file.
    n: Number of parts the file has to be split.
    """

    file_ = None
    try:
      file_   = open(filename, 'rb')
    except IOError:
        print "ERROR: opening %s" % (filename)
        exit(1)

    f_parts = []
    # File size in bytes.
    file_size = path.getsize(filename)
    # No. of bytes for each file part.
    part_size =  file_size / n
    # Take note of remaining bytes; this is non-zero when file_size is
    # not divisible by `n'.
    rem_bytes = file_size % n

    i = 0
    while i < n:
        f_parts.append(file_.read(part_size))
        i += 1

    # read the remaining bytes into the last file part.
    f_parts[n-1] += file_.read(rem_bytes)

    return f_parts


def glue_file(f_parts):
    """Glue different parts of the file to one.

    f_parts: Array containing different parts of the file. Each part
    is a sequence of bytes.
    """

    file_content = ''
    for part in f_parts:
        file_content += part

    return file_content


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
