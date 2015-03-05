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

import os

from hashlib import sha512
from os import path
from sys import exit
from glob import glob

from combox.config import get_nodedirs


def relative_path(p, config, comboxd=True):
    """Returns the relative path to the `p' w. r. t combox or node directory.

    If `comboxd' is True, the relative path is w. r. t combox
    directory.

    If `comboxd' is False, the relative path is w. r. t node
    directory.

    p: path to a directory or file.

    config: a dictionary that contains configuration information about
    combox.

    """
    if comboxd:
        directory = '%s/' % config['combox_dir']
    else:
        directory = '%s/' % get_nodedirs(config)[0]

    return p.partition(directory)[2]


def cb_path(node_path, config):
    """
    Returns abs. path of file (in combox dir.) given the node_path.
    """

    if path.isfile(node_path):
        # partition function is used to remove the `.shard.N' from the
        # file name.
        rel_file_path = relative_path(node_path,
                                      config,
                                      False).partition('.shard')[0]
        file_cb_path = path.join(config['combox_dir'],
                                 rel_file_path)
    else:
        file_cb_path = path.join(config['combox_dir'],
                                 relative_path(node_path, config, False))

    return file_cb_path


def node_path(cb_path, config):
    """Returns abs. path of file (in node dir.) given the cb_path (combox dir. path).

    If cb_path is a file, it returns the path to its first shard in
    the first node directory.

    """

    if path.isfile(cb_path):
        # partition function is used to remove the `.shard.N' from the
        # file name.
        rel_file_path = relative_path(cb_path, config)
        file_node_path = path.join(get_nodedirs(config)[0],
                                 rel_file_path)
        file_node_path = "%s.shard0" % file_node_path
    else:
        file_node_path = path.join(get_nodedirs(config)[0],
                                   relative_path(cb_path, config))

    return file_node_path


def mk_nodedir(directory, config):
    """
    Creates directory `directory' inside the nodes.

    config: a dictionary containing configuration info about combox.
    """

    nodes = get_nodedirs(config)

    rel_path = relative_path(directory, config)

    for node in nodes:
        dir_path = path.join(node, rel_path)
        try:
            os.mkdir(dir_path)
        except OSError, e:
            print e, "Something wrong. report bug to sravik@bgsu.edu"


def mk_dir(directory):
    """Creates directory"""
    try:
        os.mkdir(directory)
    except OSError, e:
        print e, "Something wrong. report bug to sravik@bgsu.edu"


def rm_nodedir(directory, config):
    """
    Removes directory `directory' inside the nodes.

    config: a dictionary containing configuration info about combox.
    """

    nodes = get_nodedirs(config)

    rel_path = relative_path(directory, config)

    for node in nodes:
        dir_path = path.join(node, rel_path)
        rm_dir(dir_path)


def rm_dir(directory):
    """Removes directory"""
    try:
        os.rmdir(directory)
    except OSError, e:
        print e, "Something wrong. report bug to sravik@bgsu.edu"


def move_nodedir(src, dest, config):
    """
    Moves directory `directory' inside the nodes from old to new location.

    src: old path to the directory
    dest: new path to the directory
    config: a dictionary containing configuration info about combox.
    """

    nodes = get_nodedirs(config)

    src_rel_path = relative_path(src, config)
    dest_rel_path = relative_path(dest, config)

    for node in nodes:
        src_dir_path = path.join(node, src_rel_path)
        dest_dir_path = path.join(node, dest_rel_path)
        try:
            os.rename(src_dir_path, dest_dir_path)
        except OSError, e:
            print e, "Something wrong. report bug to sravik@bgsu.edu"


def rm_shards(fpath, config):
    """
    Removes the file shards of `fpath' in the node directories.

    fpath: is the path to a file in the combox directory.

    config: a dictionary containing configuration info about combox.
    """

    nodes = get_nodedirs(config)

    rel_path = relative_path(fpath, config)

    for node in nodes:
        shard_glob = "%s.shard*" % path.join(node, rel_path)

        shard_glob = glob(shard_glob)
        if not len(shard_glob):
            # shard was already deleted.
            continue

        # there's always only one shard in each node directory. So,
        # the glob() will alawys return a list of size 1.
        shard = shard_glob[0]
        try:
            os.remove(shard)
        except OSError, e:
            print e, "Something wrong. report bug to sravik@bgsu.edu"


def move_shards(src, dest, config):
    """Move the shards in node directories.

    This function is used when a file is moved to different location
    inside the combox directory. It moves the shards to the
    corresponding location in the node directories.

    src: old path to the file that was moved.
    dest: new path to the file that was moved.
    config: a dictionary containing configuration info about combox.
    """

    if path.basename(src) == path.basename(dest):
        # this means the parent directory was rename, no the file
        # itself! So we don't have to do anything.
        return

    nodes = get_nodedirs(config)

    src_rel_path = relative_path(src, config)
    dest_rel_path = relative_path(dest, config)

    for node in nodes:
        src_shard_glob = "%s.shard*" % path.join(node, src_rel_path)
        # there's always only one shard in each node directory. So,
        # the glob() will alawys return a list of size 1.
        src_shard = glob(src_shard_glob)[0]

        # get shard number
        shard_no = src_shard.partition('.shard')[2]
        dest_shard = "%s.shard%s" % (path.join(node, dest_rel_path),
                                     shard_no)
        try:
            os.rename(src_shard, dest_shard)
        except OSError, e:
            print e, "Something wrong. report bug to sravik@bgsu.edu"


def purge_dir(p):
    """
    Purge everything under the given directory `p'.

    Directory `p' itself is not deleted.
    """

    p = path.abspath(p)

    if path.isfile(p):
        return os.remove(p)

    for f in os.listdir(p):
        f_path = path.join(p, f)

        if path.isfile(f_path):
            os.remove(f_path)
        else:
            purge_dir(f_path)
            os.rmdir(f_path)


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


def hash_file(filename, file_content=None):
    """Does a SHA512 hash on the contents of file.

    Returns the hexdigest of the file content's hash.

    filename: Absolute pathname of the file.
    file_content: If not None, hash of file_content is returned.
    """

    if not file_content:
        file_content = read_file(filename)

    return sha512(file_content).hexdigest()


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
