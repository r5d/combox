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

import pickledb

from os import path
from threading import Lock

from combox.file import hash_file

class ComboxSilo(object):
    """The Combox silo.

    Helps keep track of files in combox directory.
    """


    def __init__(self, config, lock):
        """config: a dictinary which contains combox configuration.

        """
        self.config = config

        self.silo_path = path.join(config['silo_dir'], 'silo.db')
        self.db = pickledb.load(self.silo_path, True)

        ## things we need for housekeep the node directory.
        self.node_dicts = ['file_created', 'file_modified', 'file_moved',
                           'file_deleted']

        # created the dicts if not already created.
        for ndict in self.node_dicts:
            if not self.db.get(ndict):
                self.db.dcreate(ndict)

        self.lock = lock


    def reload(self):
        """Re-loads the DB from disk."""
        with self.lock:
            self.db = pickledb.load(self.silo_path, True)


    def update(self, filep):
        """Update filep's info in db

        filep and the hash of its content is written to the db.

        filep: path to the file in combox directory.

        """
        self.reload()
        with self.lock:
            fhash = hash_file(filep)
            return self.db.set(filep, fhash)


    def keys(self):
        """Returns a list of all keys in db."""
        # this is why Redis or some other key-value DB should be used
        # instead of PickleDB
        self.reload()
        with self.lock:
            return self.db.db.keys()


    def remove(self, filep):
        """Removes filep from db.

        filep: path to the file in combox directory.

        """
        try:
            self.reload()
            with self.lock:
                return self.db.rem(filep)
        except KeyError, e:
            # means `filep' not present in db.
            return False


    def exists(self, filep):
        """Checks if filep's info is stored in db.

        Returns True if filep's info is in db; False otherwise.

        filep: path to the file in combox directory.

        """
        self.reload()
        with self.lock:
            if self.db.get(filep) is None:
                return False
            else:
                return True


    def stale(self, filep, fhash=None):
        """Returns True if filep's hash is different from the hash stored in db.

        Returns None, if filep's info is not yet stored in db.
        Returns False, if filep's hash has not changed it.

        filep: path to the file in combox directory.
        fhash: If not None, it is assumed to be filep's hash.
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
        """
        Returns a list containing the dicts related the the node directories.
        """
        return self.node_dicts


    def node_set(self, type_, file_):
        """
        Update information about the shard of `file_'.

        type_: 'file_created', 'file_modified', 'file_moved', 'file_deleted'
        file_: path of the file_ in combox directory.
        """

        self.reload()
        with self.lock:
            try:
                num = self.db.dget(type_, file_)
                num += 1
            except KeyError, e:
                # means file_ is not already there, so:
                num = 1
            self.db.dadd(type_, (file_, num))


    def node_get(self, type_, file_):
        """
        Returns a number denoting the number of node directories in which the file_'s shard was created/modified/moved/deleted.

        type_: 'file_created', 'file_modified', 'file_moved', 'file_deleted'
        file_: path of the file_ in combox directory.
        """
        self.reload()
        with self.lock:
            try:
                return self.db.dget(type_, file_)
            except KeyError, e:
                # file_ info not there under type_ dict.
                return None
