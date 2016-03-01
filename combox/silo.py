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

import pickledb

from os import path
from threading import Lock

from combox.file import hash_file


class ComboxSilo(object):
    """Helps keep track of files in combox directory.

    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :param threading.Lock lock:
        Lock used by :class:`.ComboxDirMonitor` and
        :class:`.NodeDirMonitor` to access this object.

    """

    def __init__(self, config, lock):
        """Initialize ComboxSilo.

        """
        self.config = config

        self.silo_path = path.join(config['silo_dir'], 'silo.db')
        self.db = pickledb.load(self.silo_path, True)

        ## things we need for housekeep the node directories
        self.node_dicts = ['file_created', 'file_modified', 'file_moved',
                           'file_deleted', 'file_moved_info']
        """List of names of dictionaries stored in DB to housekeep the node
           directories.

        Initialized to::

            ['file_created', 'file_modified', 'file_moved',
             'file_deleted', 'file_moved_info']

        when :class:`ComboxSilo` object is created.

        """

        # created the dicts if not already created.
        for ndict in self.node_dicts:
            if not self.db.get(ndict):
                self.db.dcreate(ndict)

        self.lock = lock


    def reload(self):
        """Re-loads the DB from disk.

        """
        with self.lock:
            self.db = pickledb.load(self.silo_path, True)


    def update(self, filep):
        """Update filep's info in DB.

        Path of `filep` and the hash of its content is written to the
        DB.

        :param str filep:
            Path to the file under the combox directory.
        :returns: `True`
        :rtype: bool

        """
        self.reload()
        with self.lock:
            fhash = hash_file(filep)
            return self.db.set(filep, fhash)


    def keys(self):
        """Returns list of file' paths tracked by combox.

        :returns:
            List of file paths of files tracked by combox.
        :rtype:
            `True`

        """
        # this is why Redis or some other key-value DB should be used
        # instead of PickleDB
        self.reload()
        with self.lock:
            return self.db.db.keys()


    def remove(self, filep):
        """Removes `filep` from DB.

        :param str filep:
            Path to a file under combox directory whose information
            has to be removed from the DB.
        :returns:
            Returns `False` if `filep` is not present in the DB; `True`
            otherwise.
        :rtype: bool

        """
        try:
            self.reload()
            with self.lock:
                return self.db.rem(filep)
        except KeyError, e:
            # means `filep' not present in db.
            return False


    def exists(self, filep):
        """Checks if filep's info is stored in DB.

        :param str filep:
            Path to a file under the  combox directory.
        :returns:
            Returns `True` if filep's info is in DB; `False` otherwise.
        :rtype: bool

        """
        self.reload()
        with self.lock:
            if self.db.get(filep) is None:
                return False
            else:
                return True


    def stale(self, filep, fhash=None):
        """Checks if filep's info in the DB is outdated.

        :param str filep:
            Path to a file under the combox directory.
        :param bool fhash:
            If not `None`, it is assumed to be filep's hash.
        :returns:
            Returns `True`, if filep's hash is outdated; `False` if
            filep's hash is correct; `None` if filep's info is not yet
            stored in DB.
        :rtype: bool

        """
        if not fhash:
            fhash = hash_file(filep)

        self.reload()
        with self.lock:
            fhash_in_db = self.db.get(filep)

        if fhash_in_db is None:
            return None
        elif fhash == fhash_in_db:
            return False
        else:
            return True


    def nodedicts(self):
        """Returns :attr:`node_dicts`

        """
        return self.node_dicts


    def node_set(self, type_, file_, num=-1):
        """Update information about the shard of `file_` in dictionary `type_` in the DB.

        :param str type_:
            The name of the dictinary in DB. It must be one of the
            following values: `file_created`, `file_modified`,
            `file_moved`, `file_deleted`.
        :param str file_:
            Path of the file under the combox directory.
        :param int num:
            Integer associated with the `file_`.

        """

        self.reload()
        with self.lock:
            if num != -1:
                self.db.dadd(type_, (file_, num))
                return
            try:
                num = self.db.dget(type_, file_)
                num += 1
            except KeyError, e:
                # I don't think this is the right way to do this. :|
                #
                # If we are here it means file_ is not already there,
                # so:
                num = 1
            self.db.dadd(type_, (file_, num))


    def node_store_moved_info(self, src_path, dest_path):
        """
        Make note of a file/directory moved from `src_path` to `dest_path`.

        :param str src_path:
            The source path of the file being moved.
        :param str dest_path:
            The destination path of the file being moved.

        """
        self.reload()
        with self.lock:
            self.db.dadd('file_moved_info', (src_path, dest_path))


    def node_get(self, type_, file_):
        """Returns a number denoting the number of node directories in which the `file_`'s shards was created/modified/moved/deleted.

        :param str type_:
            The name of the dictinary in DB. It must be one of the
            following values: `file_created`, `file_modified`,
            `file_moved`, `file_deleted`.
        :param str file_:
            Path of the file under the combox directory.
        :returns:
            Number denoting the number of node directories in which
            the `file_`' shards were created/modified/moved/deleted.
        :rtype: int

        """
        self.reload()
        with self.lock:
            try:
                return self.db.dget(type_, file_)
            except KeyError, e:
                # file_ info not there under type_ dict.
                return None


    def node_rem(self, type_, file_):
        """Removes information about the shards of `file_` in the `type_` dictionary in DB.

        :param str type_:
            The name of the dictinary in DB. It must be one of the
            following values: `file_created`, `file_modified`,
            `file_moved`, `file_deleted`.
        :param str file_:
            Path of the file under the combox directory.

        """
        self.reload()
        with self.lock:
            try:
                return self.db.dpop(type_, file_)
            except KeyError, e:
                # means file_'s info was already removed.
                # do nothing
                pass
