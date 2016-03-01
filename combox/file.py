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

import os

from hashlib import sha512
from os import path
from sys import exit
from glob import glob

from combox.config import get_nodedirs
from combox.log import log_e


def relative_path(p, config, comboxd=True):
    """Returns the relative path to the `p` w. r. t combox or node directory.

    :param str p:
        Path to a directory or file.
    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :param bool comboxd:
        True if `p` is a path relative to combox directory.
    :returns:
        Path relative to combox directory if `comboxd` is `True`,
        otherwise returns path relative to the node directory.
    :rtype: str
    :raises ValueError:
        If path `p` is not under the combox directory or the node
        directory.

    """
    directory = None
    if comboxd:
        directory = '%s/' % config['combox_dir']
    else:
        for node in get_nodedirs(config):
            if p.startswith(node):
                directory = '%s/' % node

    if directory is None:
        err_msg = "invalid path %s" % p
        raise ValueError, err_msg

    return p.partition(directory)[2]


def cb_path(node_path, config):
    """Returns absolute path of file/directory under the combox directory.

    :param str node_path:
        Path to a file/directory under a node directory.
    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :returns:
        Returns the corresponding path to the file/directory under the
        combox directory.
    :rtype: str

    """
    if node_path[:-1].endswith('shard'):
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


def node_path(cb_path, config, isfile):
    """Returns abs. path of file/directory in node directory.

    :param str cb_path:
        Path to a file/directory under the combox directory.
    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :param bool isfile:
        True if `cb_path` is not a directory.
    :returns:
        If `cb_path` is a file, it returns the path to its shard under
        the first node directory.

        If `cb_path` is a directory, it returns the corresponding path
        to this directory under the first node directory.
    :rtype: str

    """
    if isfile:
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


def node_paths(cb_path, config, isfile):
    """Returns a list of abs. paths of a file/directory in node directories.

    :param str cb_path:
        Path to a file/directory under the combox directory.
    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :param bool isfile:
        True if `cb_path` is not a directory.
    :returns:
        If `cb_path` is a file, it returns a list of paths to its
        shards under the node directories.

        If `cb_path` is a directory, it returns a list its
        corresponding paths under the node directories.
    :rtype: list

    """

    n_paths = []
    nodes = get_nodedirs(config)
    rel_path = relative_path(cb_path, config)

    if isfile:
        shard_no = 0
        for node in nodes:
            file_shard = '%s.shard%d' % (rel_path, shard_no)
            n_path = path.join(node, file_shard)
            n_paths.append(n_path)
            shard_no += 1
    else:
        for node in nodes:
            n_path = path.join(node, rel_path)
            n_paths.append(n_path)

    return n_paths


def mk_nodedir(directory, config):
    """Creates directory `directory` under all the node directories.

    :param str directory:
        Path to a directory under the combox directory.
    :param dict config:
        A dictionary that contains configuration information about
        combox.

    """
    nodes = get_nodedirs(config)

    rel_path = relative_path(directory, config)

    for node in nodes:
        dir_path = path.join(node, rel_path)
        mk_dir(dir_path)


def mk_dir(directory):
    """Creates a directory.

    :param str directory:
        Path to a directory to create.

    """
    try:
        os.mkdir(directory)
    except OSError, e:
        log_e("Error when trying to make directory %s" % directory)


def rm_nodedir(directory, config):
    """Removes directory `directory` under all the node directories.

    :param str directory:
        Path to a directory under the combox directory.
    :param dict config:
        A dictionary that contains configuration information about
        combox.

    """
    nodes = get_nodedirs(config)

    rel_path = relative_path(directory, config)

    for node in nodes:
        dir_path = path.join(node, rel_path)
        rm_path(dir_path)


def rm_path(fpath):
    """Removes path `fpath`.

    :param str fpath:
        It can be a file or an empty directory.
    """
    try:
        if path.isfile(fpath):
            os.remove(fpath)
        elif path.isdir(fpath):
            purge_dir(fpath)
            os.rmdir(fpath)
    except OSError, e:
        log_e("Error when trying to remove path %s" % fpath)


def move_nodedir(src, dest, config):
    """Moves directory `src` to `dest`.

    :param str src:
         Old path to the directory.
    :param str dest:
         New path to the directory
    :param dict config:
        A dictionary that contains configuration information about
        combox.

    """
    nodes = get_nodedirs(config)

    src_rel_path = relative_path(src, config)
    dest_rel_path = relative_path(dest, config)

    for node in nodes:
        src_dir_path = path.join(node, src_rel_path)
        dest_dir_path = path.join(node, dest_rel_path)
        try:
            os.renames(src_dir_path, dest_dir_path)
        except OSError, e:
            log_e("Error when trying to rename %s -> %s" % (src_dir_path, dest_dir_path))


def rm_shards(fpath, config):
    """Removes the file shards of `fpath` under the node directories.

    :param str fpath:
         Path to file under the combox directory.
    :param dict config:
        A dictionary that contains configuration information about
        combox.

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
            log_e("Error when trying to remove shard %s" % shard)


def move_shards(src, dest, config):
    """Move the shards in node directories.

    This function is used when a file is moved to different location
    inside the combox directory. It moves the shards of the respective
    file to the new location under the node directories.

    :param str src:
        Old path to the file that was moved under the combox directory.
    :param str dest:
        New path to the file that was moved under the combox directory.
    :param dict config:
        A dictionary that contains configuration information about
        combox.

    """
    nodes = get_nodedirs(config)

    src_rel_path = relative_path(src, config)
    dest_rel_path = relative_path(dest, config)

    for node in nodes:
        src_shard_glob = "%s.shard*" % path.join(node, src_rel_path)
        # there's always only one shard in each node directory.
        glob_list = glob(src_shard_glob)
        if glob_list:
            src_shard = glob_list[0]
        else:
            # shards are not there!, so we return.
            return

        # get shard number
        shard_no = src_shard.partition('.shard')[2]
        dest_shard = "%s.shard%s" % (path.join(node, dest_rel_path),
                                     shard_no)
        try:
            os.renames(src_shard, dest_shard)
        except OSError, e:
            log_e("Error when trying to rename shard %s -> %s" % (src_shard, dest_shard))


def purge_dir(p):
    """
    Purge everything under the given directory `p`.

    Directory `p` itself is not deleted.

    :param str p:
        Path to directory that needs to be purged.
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
    """Split `data` into `n` parts and return them as a list.

    :param str data:
        Stream of bytes or string.
    :param int n:
        Number of parts the `data` has to be split.
    :returns:
        List of strings -- the `data` divided into `n` parts.
    :rtype: list

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
    """Glue different parts of the `data` into a single whole.

    :param list d_parts:
        List containing different parts of the `data`. Each part is a
        sequence of bytes.
    :returns:
        The `data` glued into a single whole.
    :rtype: str

    """
    data = ''
    for part in d_parts:
        data += part

    return data


def read_file(filename):
    """Read file `filename` and return it as a string.

    :param str filename:
        Absolute pathname of the file.
    :returns:
        Content of file `filename` as a string.
    :rtype: str

    """
    file_ = None
    content = ''

    with open(filename, 'rb') as f:
        for line in f:
            content = content + line

    return content


def hash_file(filename, file_content=None):
    """Does a SHA512 hash on the contents of file.

    Returns the hexdigest of the file content's hash.

    :param str filename:
        Absolute pathname of the file.
    :param str file_content:
        If not ``None``, SHA512 hash of `file_content` is returned.
    :returns:
        If `file_content` is ``None``, returns the SHA512 hash of
        contents of file `filename`.

        If `file_content` is not ``None``, returns the SHA512 hash of
        `file_content`.
    :rtype: str
    """

    if not file_content:
        file_content = read_file(filename)

    return sha512(file_content).hexdigest()


def write_file(filename, filecontent):
    """Write `filecontent` to `filename`.

    :param str filename:
        Absolute pathname of the file.
    :param str filecontent:
        Data to write to `filename`.

    """
    file_ = None
    try:
      file_   = open(filename, 'wb')
      file_.write(filecontent)
      file_.close()
    except IOError:
        log_e("Error creating and writing content to %s" % filename)
        exit(1)


def write_shards(shards, directories, shard_basename):
    """Write shards to node directories.

    :param list shards:
        List of strings (data).
    :param list directories:
        List of paths of node directories.
    :param str shard_basename:
        Base name for the shards.

    """
    shard_no = 0
    for directory in directories:
        # partial filename of the shard
        p_filename =  path.join(directory, shard_basename)
        shard_name =  "%s.shard%s" % (p_filename, shard_no)
        write_file(shard_name, shards[shard_no])
        shard_no += 1


def read_shards(directories, shard_basename):
    """Read the shards of a file from node directories and return it as a list.

    :param list directories:
        List of paths of node directories from which to read the
        shards.
    :param str shard_basename:
        Base name for the shards; the canonical file name.
    :returns:
        List of contents of the shards of the file with basename
        `shard_basename`.

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


def no_of_shards(cb_path, config):
    """Returns the no. of shards that exists for `cb_path` under the node directories.

    :param str cb_path:
        Path to a file under the combox directory.
    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :returns:
        The number of shards that exists for the file `cb_path`.
    :rtype: int

    """
    no_shards_there = 0
    shard_paths = node_paths(cb_path, config, isfile=True)

    for shard in shard_paths:
        if path.isfile(shard):
            no_shards_there += 1

    return no_shards_there
