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

from watchdog.events import FileSystemEventHandler

from combox.crypto import split_and_encrypt
from combox.file import (mk_nodedir, rm_nodedir, rm_shards,
                         relative_path, move_shards, move_nodedir)


class ComboxEventHandler(FileSystemEventHandler):
    """Monitors Combox directory for changes and does its crypto thing.

    """

    def __init__(self, config):
        """
        config: a dictinary which contains combox configuration.
        """
        self.config = config

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')


    def on_moved(self, event):
        super(ComboxEventHandler, self).on_moved(event)

        if event.is_directory:
            # creates a corresponding directory at the node dirs.
            move_nodedir(event.src_path, event.dest_path, self.config)
            # TODO: code for updating files under the renamed
            # directory in YAML silo.
        else:
            # file moved
            move_shards(event.src_path, event.dest_path, self.config)
            # TODO: code for updating file info in YAML silo.

        type_ = 'directory' if event.is_directory else 'file'
        logging.info("Moved %s: from %s to %s", type_, event.src_path,
                    event.dest_path)


    def on_created(self, event):
        super(ComboxEventHandler, self).on_created(event)

        if event.is_directory:
            # creates a corresponding directory at the node dirs.
            mk_nodedir(event.src_path, self.config)
        else:
            # file was created
            split_and_encrypt(event.src_path, self.config)
            # TODO: code for storing file info in YAML silo.

        type_ = 'directory' if event.is_directory else 'file'
        logging.info("Created %s: %s", type_, event.src_path)


    def on_deleted(self, event):
        super(ComboxEventHandler, self).on_deleted(event)

        if event.is_directory:
            # Delete corresponding directory in the nodes.
            rm_nodedir(event.src_path, self.config)
        else:
            # remove the corresponding file shards in the node
            # directories.
            rm_shards(event.src_path, self.config)
            # TODO: code for removing file info from YAML silo.

        type_ = 'directory' if event.is_directory else 'file'
        logging.info("Deleted %s: %s", type_, event.src_path)


    def on_modified(self, event):
        super(ComboxEventHandler, self).on_modified(event)

        if event.is_directory:
            # do nothing
            pass
        else:
            # file was modified
            split_and_encrypt(event.src_path, self.config)
            # TODO: code for updating file info in YAML silo.

        type_ = 'directory' if event.is_directory else 'file'
        logging.info("Modified %s: %s", type_, event.src_path)
