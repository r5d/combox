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
import logging

from os import path

from watchdog.events import LoggingEventHandler

from combox.config import get_nodedirs
from combox.crypto import split_and_encrypt, decrypt_and_glue
from combox.file import (mk_nodedir, rm_nodedir, rm_shards,
                         relative_path, move_shards, move_nodedir,
                         cb_path, node_path, hash_file, rm_path,
                         node_paths)
from combox.silo import ComboxSilo


class ComboxDirMonitor(LoggingEventHandler):
    """Monitors Combox directory for changes and does its crypto thing.

    """

    def __init__(self, config):
        """
        config: a dictinary which contains combox configuration.
        """
        super(ComboxDirMonitor, self).__init__()

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        self.config = config
        self.silo = ComboxSilo(self.config)

        self.housekeep()


    def silo_update(self):
        """
        Re-reads the silo from disk.
        """
        self.silo = ComboxSilo(self.config)


    def housekeep(self):
        """Recursively traverses combox directory, discovers changes and updates silo and node directories.

        Information about files that have been removed from combox
        directory is purged from the silo. Also the corresponding
        shards are removed from the node directories.

        The untracked files are encrypted and split between the node
        directories and information about these files are stashed in
        the silo.

        Information about modified files in the combox directory are
        updated and the file's shards are updated.

        """
        self.silo_update()
        print "combox is housekeeping."
        print "Please don't make any changes to combox directory now."
        print "Thanks for your patience."

        # Remove information about files that were deleted.
        for fpath in self.silo.keys():
            if not path.exists(fpath):
                # remove this file's info from silo.
                print fpath, "was deleted. Removing it from DB."
                self.silo.remove(fpath)
                # also purge the file's shards in node directories.
                rm_shards(fpath, self.config)

        # Add/update information about files that were created/modded.
        # Also do split_and_encrypt on files that were created/modded.
        for root, dirs, files in os.walk(self.config['combox_dir']):

            for f in files:
                fpath = path.join(root, f)

                if (self.silo.exists(fpath) and
                    self.silo.stale(fpath)):
                    # file was modified
                    print fpath, "was modified. Updating DB and shards..."
                    split_and_encrypt(fpath, self.config)
                    self.silo.update(fpath)
                elif not self.silo.exists(fpath):
                    # new file
                    print 'Adding new file', fpath, '...'
                    split_and_encrypt(fpath, self.config)
                    self.silo.update(fpath)


        print "combox is done with the drudgery."
        print "Do what you want to the combox directory."


    def on_moved(self, event):
        super(ComboxDirMonitor, self).on_moved(event)
        self.silo_update()

        if event.is_directory:
            # creates a corresponding directory at the node dirs.
            move_nodedir(event.src_path, event.dest_path, self.config)
        else:
            # file moved
            move_shards(event.src_path, event.dest_path, self.config)
            # update file info in silo.
            self.silo.remove(event.src_path)
            self.silo.update(event.dest_path)


    def on_created(self, event):
        super(ComboxDirMonitor, self).on_created(event)
        self.silo_update()

        file_node_path = node_path(event.src_path, self.config,
                                   not event.is_directory)

        if event.is_directory and (not path.exists(file_node_path)):
            # creates a corresponding directory at the node dirs.
            mk_nodedir(event.src_path, self.config)
        elif (not event.is_directory) and (not path.exists(
                file_node_path)):
            # file was created
            split_and_encrypt(event.src_path, self.config)
            # store file info in silo.
            self.silo.update(event.src_path)


    def on_deleted(self, event):
        super(ComboxDirMonitor, self).on_deleted(event)
        self.silo_update()

        file_node_path = node_path(event.src_path, self.config,
                                   not event.is_directory)

        if event.is_directory and (path.exists(file_node_path)):
            # Delete corresponding directory in the nodes.
            rm_nodedir(event.src_path, self.config)
        elif(not event.is_directory) and (path.exists(file_node_path)):
            # remove the corresponding file shards in the node
            # directories.
            rm_shards(event.src_path, self.config)
            # remove file info from silo.
            self.silo.remove(event.src_path)


    def on_modified(self, event):
        super(ComboxDirMonitor, self).on_modified(event)
        self.silo_update()

        if event.is_directory:
            # do nothing
            pass
        else:
            # file was modified
            split_and_encrypt(event.src_path, self.config)
            # update file info in silo.
            self.silo.update(event.src_path)


class NodeDirMonitor(LoggingEventHandler):
    """Monitors Node directory for changes and does its crypto thing.

    """

    def __init__(self, config):
        """
        config: a dictinary which contains combox configuration.
        """
        super(NodeDirMonitor, self).__init__()

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        self.config = config
        self.silo = ComboxSilo(self.config)


    def silo_update(self):
        """
        Re-reads the silo from disk.
        """
        self.silo = ComboxSilo(self.config)


    def shardp(self, path):
        """Returns True if `path' is a shard

        Shards end with `.shardN' where `N' is a natural number.
        """
        if path[:-1].endswith('.shard'):
            return True
        else:
            return False


    def housekeep(self):
        """Recursively traverses node directory, discovers changes and updates silo and combox directory.

        If it detects that a shard was deleted, it purges the
        corresponding file from the combox director and also removes
        information about the file from the silo.

        If it detects new shards, it reconstructs the file and places
        it at the corresponding location in the combox directory.

        If it detects shards have been modified, it reconstructs the
        file and places the modified file at the corresponding
        location in the combox directory.

        """
        self.silo_update()

        print "combox node monitor is housekeeping."
        print "Please don't make any changes to combox directory now."
        print "Thanks for your patience."

        # Remove files from the combox directory whose shards were
        # deleted.
        for fpath in self.silo.keys():
           fshards = node_paths(fpath, self.config, True)

           for fshard in fshards:
               if not path.exists(fshard):
                   # remove the file from combox directory.
                   rm_path(fpath)
                   print fpath, "was deleted on another computer. Removing it."
                   # update silo.
                   self.silo.remove(fpath)
                   break

        for root, dirs, files in os.walk(get_nodedirs(self.config)[0]):
            for f in files:
                shard = path.join(root, f)

                if not self.shardp(shard):
                    continue

                file_cb_path = cb_path(shard, self.config)
                if not self.silo.exists(file_cb_path):
                    print file_cb_path, "was created remotely. Creating it locally now..."
                    decrypt_and_glue(file_cb_path, self.config)
                    self.silo.update(file_cb_path)
                elif self.silo.exists(file_cb_path):
                    file_content = decrypt_and_glue(file_cb_path,
                                                    self.config,
                                                    write=False)
                    file_content_hash = hash_file(file_cb_path, file_content)

                    if self.silo.stale(file_cb_path, file_content_hash):
                        # file modified
                        print file_cb_path, "modified remotely. Updating local copy."
                        decrypt_and_glue(file_cb_path, self.config)
                        self.silo.update(file_cb_path)


        print "combox node monitor is done with the drudgery."
        print "Do what you want to the combox directory."


    def on_moved(self, event):
        super(NodeDirMonitor, self).on_moved(event)
        self.silo_update()

        src_cb_path = cb_path(event.src_path, self.config)
        dest_cb_path = cb_path(event.dest_path, self.config)

        if not path.exists(dest_cb_path):
            # means this path was move on another computer that is
            # running combox.
            try:
                os.rename(src_cb_path, dest_cb_path)
            except OSError, e:
                print "Jeez, failed to rename path.", e

        if not event.is_directory:
            self.silo.remove(src_cb_path)
            self.silo.update(dest_cb_path)


    def on_created(self, event):
        super(NodeDirMonitor, self).on_created(event)
        self.silo_update()

        if not self.shardp(event.src_path) and not event.is_directory:
            # the file created can be ignored as it is not a shard or
            # a directory.
            return

        file_cb_path = cb_path(event.src_path, self.config)

        if event.is_directory and (not path.exists(file_cb_path)):
            # means, the directory was created on another computer
            # (also running combox). so, create this directory
            # under the combox directory
            os.mkdir(file_cb_path)
        elif (not event.is_directory) and (not path.exists(file_cb_path)):
            # shard created.

            # means, file was created on another computer (also
            # running combox). so, reconstruct the file and put it
            # in the combox directory.
            decrypt_and_glue(file_cb_path, self.config)
            # update db.
            self.silo.update(file_cb_path)


    def on_deleted(self, event):
        super(NodeDirMonitor, self).on_deleted(event)
        self.silo_update()

        if not self.shardp(event.src_path) and not event.is_directory:
            # the file created can be ignored as it is not a shard or
            # a directory.
            return

        file_cb_path = cb_path(event.src_path, self.config)

        if event.is_directory:
            # Delete corresponding directory under the combox directory.
            rm_path(file_cb_path)
        elif not event.is_directory and path.exists(file_cb_path):
            # remove the corresponding file under the combox directory.
            rm_path(file_cb_path)
            # remove file info from silo.
            self.silo.remove(file_cb_path)


    def on_modified(self, event):
        super(NodeDirMonitor, self).on_modified(event)
        self.silo_update()

        if not self.shardp(event.src_path) and not event.is_directory:
            # the file created can be ignored as it is not a shard or
            # a directory.
            return

        file_cb_path = cb_path(event.src_path, self.config)

        if event.is_directory:
            # do nothing
            pass
        elif (not event.is_directory):
            file_content = decrypt_and_glue(file_cb_path,
                                            self.config,
                                            write=False)
            file_content_hash = hash_file(file_cb_path, file_content)

            if self.silo.stale(file_cb_path, file_content_hash):
                # shard modified

                # means, file was modified on another computer (also
                # running combox). so, reconstruct the file and put it
                # in the combox directory.
                decrypt_and_glue(file_cb_path, self.config)
                # update db.
                self.silo.update(file_cb_path)
