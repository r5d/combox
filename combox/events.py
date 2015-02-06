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

from combox.crypto import split_and_encrypt
from combox.file import (mk_nodedir, rm_nodedir, rm_shards,
                         relative_path, move_shards, move_nodedir)
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

        if event.is_directory:
            # creates a corresponding directory at the node dirs.
            mk_nodedir(event.src_path, self.config)
        else:
            # file was created
            split_and_encrypt(event.src_path, self.config)
            # store file info in silo.
            self.silo.update(event.src_path)


    def on_deleted(self, event):
        super(ComboxDirMonitor, self).on_deleted(event)

        if event.is_directory:
            # Delete corresponding directory in the nodes.
            rm_nodedir(event.src_path, self.config)
        else:
            # remove the corresponding file shards in the node
            # directories.
            rm_shards(event.src_path, self.config)
            # remove file info from silo.
            self.silo.remove(event.src_path)


    def on_modified(self, event):
        super(ComboxDirMonitor, self).on_modified(event)

        if event.is_directory:
            # do nothing
            pass
        else:
            # file was modified
            split_and_encrypt(event.src_path, self.config)
            # update file info in silo.
            self.silo.update(event.src_path)
