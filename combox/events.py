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
import platform
import logging
import time

from os import path
from threading import Lock
from threading import Timer

from watchdog.events import LoggingEventHandler

from combox.config import get_nodedirs
from combox.crypto import split_and_encrypt, decrypt_and_glue
from combox.file import (mk_nodedir, rm_nodedir, rm_shards,
                         relative_path, move_shards, move_nodedir,
                         cb_path, node_path, hash_file, rm_path,
                         node_paths, no_of_shards)
from combox.log import log_i, log_e
from combox.silo import ComboxSilo


class ComboxDirMonitor(LoggingEventHandler):
    """Monitors combox directory for changes and makes corresponding changes in node directories.

     - When a file is created in the combox directory, the
       :class:`.ComboxDirMonitor` creates encrypted shards of the file
       and spreads them across the node directories.

     - When a file is modified in the combox directory, the
       :class:`.ComboxDirMonitor` updates the encrypted shards of the
       file in the node directories.

     - When a file is moved/renamed in the combox directory, the
       :class:`.ComboxDirMonitor` moves/renames the encrypted shards
       of the file in the node directories.

     - When a file is deleted in the combox directory, the
       :class:`.ComboxDirMonitor` delets the encrypted shards of the
       file in the node directories.

    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :param threading.Lock dblock:
        Lock to access the :class:`.ComboxSilo`. object.
    :param threading.Lock monitor_lock:
        Lock shared by :class:`.ComboxDirMonitor` and all the
        :class:`.NodeDirMonitor` objects.

    """

    def __init__(self, config, dblock, monitor_lock):
        """Initialize :class:`.ComboxDirMonitor`.

        """
        super(ComboxDirMonitor, self).__init__()

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        self.config = config
        self.silo = ComboxSilo(self.config, dblock)
        self.lock = monitor_lock

        # tracks files that are created during the course of this run.
        self.just_created = {}

        self.housekeep()


    def tmp_file(self, file_path):
        """Returns `True` if `file_path` is a temporary file.

        :param str file_path:
            Path of a file.
        :returns:
            `True` if `file_path` is a temporary file.
        :rtype: bool

        """
        if file_path.endswith("~"):
            return True
        elif path.basename(file_path).startswith(".#"):
            return True
        elif (path.basename(file_path).startswith("#") and
              file_path.endswith("#")):
            return True
        else:
            return False


    def housekeep(self):
        """Recursively traverses combox directory, discovers changes and updates silo and node directories. This method must **never** be called directly.

        This method is called before :class:`.ComboxDirMonitor` starts
        monitoring the combox directory.

        - First, if it finds tracked files in the combox directory
          have been deleted, it clears their information from the DB
          and it purges the encrypted shards of the respective files
          from the node directories.

        - Second, if it finds files that were modified in the combox
          directory, it updates their respective encrypted shards in
          the node directories.

        - Third, if it finds files that are not yet tracked by combox,
          it creates their respective encrypted shards and spreads
          them across the node directories.

        """
        log_i("combox monitor is housekeeping")
        log_i("Please don't make any changes to combox directory now")

        # Remove information about files that were deleted.
        fpath_filter = lambda x: x not in self.silo.nodedicts()
        fpaths = filter(fpath_filter, self.silo.keys())

        for fpath in fpaths:
            if not path.exists(fpath):
                # remove this file's info from silo.
                log_i("%s was deleted. Removing it from DB" % fpath)
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
                    log_i("%s was modified. Updating DB and shards..." % fpath)
                    split_and_encrypt(fpath, self.config)
                    self.silo.update(fpath)
                elif (not self.silo.exists(fpath)
                      and not self.tmp_file(fpath)):
                    # new file
                    log_i("Adding new file %s..." % fpath)
                    split_and_encrypt(fpath, self.config)
                    self.silo.update(fpath)


        log_i("combox monitor is done with housekeeping")
        log_i("Do what you want to the combox directory")


    def on_moved(self, event):
        """Called when a file/directory is moved/renamed in the combox directory.

        If a directory is renamed/moved, it renames/moves the
        corresponding directory in all the node directories.

        If a file is renamed/moved, it renames/moves the shards of the
        file in all the node directories and updates the DB.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`~watchdog.events.FileSystemEvent`

        """
        super(ComboxDirMonitor, self).on_moved(event)

        if event.is_directory:
            with self.lock:
                # creates a corresponding directory at the node dirs.
                move_nodedir(event.src_path, event.dest_path, self.config)
        else:
            with self.lock:
                # file moved
                move_shards(event.src_path, event.dest_path, self.config)
                # update file info in silo.
                self.silo.remove(event.src_path)
                self.silo.update(event.dest_path)


    def on_created(self, event):
        """Called when a file/directory is created in the combox directory.

        If a directory is created, it creates the corresponding
        directory in all the node directories.

        If a file is created, it:

            - Splits the file into shards.
            - Encrypts all the shards.
            - Spreads the encrypted shards across the node
              directories.
            - Store hash of the file in DB.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`~watchdog.events.FileSystemEvent`

        """
        super(ComboxDirMonitor, self).on_created(event)

        if self.tmp_file(event.src_path):
            # ignore tmp files.
            log_i("Created tmp file %s...ignoring" %
                  event.src_path)
            return

        # make note of this file creation; will be used when
        # on_modified is called after this file creatiion.
        self.just_created[event.src_path] = True

        file_node_path = node_path(event.src_path, self.config,
                                   not event.is_directory)

        if event.is_directory and (not path.exists(file_node_path)):
            with self.lock:
                # creates a corresponding directory at the node dirs.
                mk_nodedir(event.src_path, self.config)
        elif (not event.is_directory) and (not path.exists(
                file_node_path)):
            with self.lock:
                # file was created
                split_and_encrypt(event.src_path, self.config)
                # store file info in silo.
                self.silo.update(event.src_path)


    def on_deleted(self, event):
        """Called when a file/directory is deleted in the combox directory.

        If a directory is deleted, it deletes the corresponding
        directory in all the node directories.

        If a file is deleted, it deletes all of the file's shards in
        the node directories and removes information about the file in
        the DB.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`~watchdog.events.FileSystemEvent`

        """
        super(ComboxDirMonitor, self).on_deleted(event)

        file_node_path = node_path(event.src_path, self.config,
                                   not event.is_directory)

        if event.is_directory and (path.exists(file_node_path)):
            # Delete corresponding directory in the nodes.
            with self.lock:
                rm_nodedir(event.src_path, self.config)
        elif(not event.is_directory) and (path.exists(file_node_path)):
            with self.lock:
                # remove the corresponding file shards in the node
                # directories.
                rm_shards(event.src_path, self.config)
                # remove file info from silo.
                self.silo.remove(event.src_path)


    def on_modified(self, event):
        """Called when a file/directory is modified in the combox directory.

        If a directory is modified, nothing is done.

        If a file is modified, it:

            - Splits the file into shards.
            - Encrypts all the shards.
            - Spreads the encrypted shards across the node
              directories, replacing the ol' shards.
            - Update the hash of the file stored in the DB.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`~watchdog.events.FileSystemEvent`

        """
        super(ComboxDirMonitor, self).on_modified(event)

        if self.tmp_file(event.src_path):
            # ignore tmp files.
            log_i("Modified tmp file %s...ignoring" %
                  event.src_path)
            return

        if event.is_directory:
            # do nothing
            pass
        else:
            # file was modified
            with self.lock:
                f_size_MiB = path.getsize(event.src_path) / 1048576.0
                log_i('%s modified %f' % (event.src_path, f_size_MiB))

                # introduce delay to prevent multiple "file modified"
                # events from being generated.
                if f_size_MiB >= 30:
                    sleep_time = (f_size_MiB / 30.0)
                    log_i("waiting on_modified combox monitor %f" % sleep_time)
                    time.sleep(sleep_time)
                    log_i("end waiting on_modified combox monitor")
                else:
                    time.sleep(1)

                # watchdog's weirdness
                # --------------------
                #
                # On GNU/Linux, when a file is created, watchdog
                # generates a 'file created' and a 'file modified'
                # event; we're tracking this behaviour and ignoring
                # the 'file modified' event.
                #
                if (self.just_created.has_key(event.src_path) and
                    self.just_created[event.src_path] and
                    platform.system() == 'Linux'):
                    self.just_created[event.src_path] = False
                    log_i("Just created file %s. So ignoring on_modified call." % (
                        event.src_path))
                    return

                split_and_encrypt(event.src_path, self.config)
                # update file info in silo.
                self.silo.update(event.src_path)


class NodeDirMonitor(LoggingEventHandler):
    """Monitors a node directory for changes and makes corresponding changes in the combox directory.

    An instance of :class:`.NodeDirMonitor` is created for each node
    directory; so, if there are two node directories, two instances of
    this class must be created.

    - When a shard is created in the node directory by virtue of a
      file created in the combox directory located in *another*
      computer, the :class:`.NodeDirMonitor` glues the decrypted
      version of all the shards (of a file) in the node directories
      and puts the glued file in the combox directory of *this*
      computer.

    - When a shard is modified in the node directory by virtue of a
      file modified in the combox directory located in *another*
      computer, the :class:`.NodeDirMonitor`, glues the decrypted
      version of all the shards (of a file) in the node directories
      and puts the updated glued file in the combox directory of
      *this* computer.

    - When a shard is moved/renamed in the node directory by virtue of
      the corresponding file moved/renamed in the combox directory
      located in *another* computer, the :class:`.NodeDirMonitor`
      moves/renames all the shards (of a file) in the node
      directories.

    - When a shard is deleted in the node directory by virtue of the
      corresponding file deleted in the combox directory located in
      *another* computer, the :class:`.NodeDirMonitor` deletes all the
      shards (of a file) in the node directories.


    :param dict config:
        A dictionary that contains configuration information about
        combox.
    :param threading.Lock dblock:
        Lock to access the :class:`.ComboxSilo`. object.
    :param threading.Lock monitor_lock:
        Lock shared by :class:`.ComboxDirMonitor` and all the
        :class:`.NodeDirMonitor` objects.

    """

    def __init__(self, config, dblock, monitor_lock):
        """Initialize :class:`.NodeDirMonitor`.

        """
        super(NodeDirMonitor, self).__init__()

        self.lock = monitor_lock
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        self.config = config
        self.silo = ComboxSilo(self.config, dblock)

        self.num_nodes = len(get_nodedirs(self.config))

        # track file shards that are just created during this run.
        self.just_created = {}


    def shardp(self, path):
        """Checks if `path` is a shard.

        Shards end with `.shardN` where `N` is a natural number.

        :returns:
            Returns `True` if `path` is a shard; `False` otherwise.
        :rtype: bool

        """
        if path[:-1].endswith('.shard'):
            return True
        else:
            return False


    def delete_later(self, file_cb_path):
        """Delete `file_cb_path` if its  still under 'file_deleted' dictionary in DB.

        This is used by the :meth:`~.NodeDirMonitor.on_deleted` method.

        This is a workaround to make combox predict official Google
        Drive client's behavior.
        """
        with self.lock:
            num = self.silo.node_get('file_deleted', file_cb_path)

            if num == self.num_nodes:
                log_i("Deleting %s..." % file_cb_path)
                # remove the corresponding file under the combox
                # directory.
                rm_path(file_cb_path)
                # remove file info from silo.
                self.silo.remove(file_cb_path)
                self.silo.node_rem('file_deleted', file_cb_path)


    def housekeep(self):
        """Recursively traverses node directory, discovers changes and updates silo and combox directory. This method must **never** be called directly.

        This method is called before :class:`.NodeDirMonitor` starts
        monitoring the node directory.

        - First, if it finds a shard of a tracked file deleted in the
          node directory, it deletes the respective file in the combox
          directory and removes the file's information from the DB,
          iff the shards of this file has been removed in all other
          node directories too.

        - Second, if it finds a shard of a file that is not tracked in
          the node directory, it resurrects the file from the shards,
          writes it to the combox directory, and stores the file's
          information in the DB, iff all of the shards of this file
          are found in the node directories.

        """
        log_i("combox node monitor is housekeeping")
        log_i("Please don't make any changes to combox directory now")

        # Remove files from the combox directory whose shards were
        # deleted.
        # Remove information about files that were deleted.
        fpath_filter = lambda x: x not in self.silo.nodedicts()
        fpaths = filter(fpath_filter, self.silo.keys())

        for fpath in fpaths:
            del_num = 0
            fshards = node_paths(fpath, self.config, True)

            for fshard in fshards:
                if not path.exists(fshard):
                    del_num += 1

            if del_num == self.num_nodes:
                # remove the file from combox directory.
                rm_path(fpath)
                log_i("%s was deleted on another computer. Removing it" %
                      fpath)
                # update silo.
                self.silo.remove(fpath)
                self.silo.node_rem('file_deleted', fpath)
            elif del_num > 0:
                # means, all the shards of the file have not been
                # deleted yet, so, we store the no. of shards was
                # deleted in the 'file_deleted' dict inside the silo.
                self.silo.node_set('file_deleted', fpath, del_num)

        # Re-construct files created on another computer when combox
        # was switched off. Only files who's all the shards have made
        # it to the node directories are re-constructed.

        # Dict that keeps track of the files that were created.
        files_created = {}
        for node_dir in get_nodedirs(self.config):
            for root, dirs, files in os.walk(node_dir):
                for f in files:
                    shard = path.join(root, f)

                    if (not self.shardp(shard) or
                        '.dropbox.cache' in shard):
                        continue

                    file_cb_path = cb_path(shard, self.config)
                    if not self.silo.exists(file_cb_path):
                        if not files_created.get(file_cb_path):
                            files_created[file_cb_path] = 1
                        else:
                            files_created[file_cb_path] += 1

        for f_cb_path, crt_num in files_created.items():
            if crt_num == self.num_nodes:
                log_i("%s was created remotely. Creating it locally now..." %
                      f_cb_path)
                decrypt_and_glue(f_cb_path, self.config)
                # update silo.
                self.silo.update(f_cb_path)
                self.silo.node_rem('file_created', f_cb_path)
            elif crt_num > 0:
                # means, all the shards of the file have not arrived
                # yet, so, we store the no. of shards that did arrive
                # in the 'file_created' dict inside the silo.
                self.silo.node_set('file_created', f_cb_path, crt_num)

        log_i("combox node monitor with housekeeping")
        log_i("Do what you want to the combox directory")


    def on_moved(self, event):
        """Called when a shard/directory is moved/renamed in the node directory.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`~watchdog.events.FileSystemEvent`
        """
        super(NodeDirMonitor, self).on_moved(event)

        src_cb_path = cb_path(event.src_path, self.config)
        dest_cb_path = cb_path(event.dest_path, self.config)

        silo_node_dict = 'file_moved'
        cb_filename = src_cb_path

        if (not self.shardp(event.src_path) and
            not self.shardp(event.dest_path) and
            not event.is_directory):
            # The file moved is of no importance.
            return
        elif (not self.shardp(event.src_path) and
              self.shardp(event.dest_path) and
              not path.exists(dest_cb_path) and
              not event.is_directory):
            # This is Dropbox specific.
            #
            # Temp. file inside .dropbox.cache is renamed to a shard;
            # so this the first time the shard appears in this node
            # directory -- it is created.
            log_i("Got it! %s was created" % event.dest_path)
            silo_node_dict = 'file_created'
            cb_filename = dest_cb_path
        elif (self.shardp(event.src_path) and
              self.shardp(event.dest_path) and
              '.dropbox.cache' in event.dest_path and
              not event.is_directory):
            # This is Dropbox specific :|
            #
            # The shard is moved to the Dropbox's cache. This is
            # happens when a shard is either deleted or modified in
            # the Dropbox directory.
            #
            # When here we cannot tell whether the shard is
            # deleted/modified. So, first we assume that the file is
            # deleted and store this assumption in the silo[1].
            #
            # If the shard is being modified, then next Dropbox moves
            # the modified version of the shard from its cache
            # ('.dropbox.cache/' directory under the Dropox
            # directory); this we catch in the next 'elif' statement.
            silo_node_dict = 'file_deleted'
            with self.lock:
                # [1]: Store the assumption in silo.
                log_i("Assuming %s (%s) is deleted" %
                      (cb_filename, event.src_path))
                self.silo.node_set(silo_node_dict, cb_filename)
                num = self.silo.node_get(silo_node_dict, cb_filename)
                if num == self.num_nodes:
                    # If here, then our assumption that the file is
                    # deleted is true.
                    rm_path(cb_filename)
                    # remove file info from silo.
                    self.silo.remove(cb_filename)
                    self.silo.node_rem(silo_node_dict, cb_filename)
            return
        elif (not self.shardp(event.src_path) and
              self.shardp(event.dest_path) and
              path.exists(dest_cb_path) and
              not event.is_directory):
            # This is Dropbox specific :|
            #
            # Okay, if we are here that means the shard was actually
            # being modified, so our previous assumption that it was
            # deleted was wrong, so we remove that information from
            # the silo.
            cb_filename = dest_cb_path
            with self.lock:
                log_i("Okay, %s (%s) was actually modified" %
                      (cb_filename, event.dest_path))
                self.silo.node_rem('file_deleted', cb_filename)
                # Next, if we're on GNU/Linux, watchdog detects that
                # the shard was modified and generates calls the
                # on_modified method. So we don't have to store
                # information in the silo about this shard being
                # modified; we do that later in the on_modified
                # method.
                #
                # But, on OS X (a.k.a Darwin), watchdog detect the
                # shard is modified and does not generate a call to
                # the on_modified method. So we store the information
                # about the modified shard here itself.
                if platform.system() == 'Darwin':
                    self.silo.node_set('file_modified', cb_filename)
                    num = self.silo.node_get('file_modified', cb_filename)
                    if num == self.num_nodes:
                        decrypt_and_glue(cb_filename, self.config)
                        # update db.
                        self.silo.update(cb_filename)
                        self.silo.node_rem('file_modified', cb_filename)
            return


        if not path.exists(dest_cb_path):
            # means this path was moved on another computer that is
            # running combox.
            with self.lock:
                self.silo.node_set(silo_node_dict, cb_filename)
                num = self.silo.node_get(silo_node_dict, cb_filename)
                if num != self.num_nodes:
                    return
                elif silo_node_dict == 'file_created':
                    # This is Dropbox specific :|
                    # create file in cb directory.
                    log_i("Creating %s..." % cb_filename)
                    decrypt_and_glue(cb_filename, self.config)
                    # update db.
                    self.silo.update(cb_filename)
                    self.silo.node_rem('file_created', cb_filename)
                    return
                else:
                    try:
                        os.renames(src_cb_path, dest_cb_path)
                    except OSError, e:
                        log_e("Jeez, failed to rename path. %r" % e)
                    self.silo.node_rem(silo_node_dict, src_cb_path)

        if not event.is_directory:
            self.silo.remove(src_cb_path)
            self.silo.update(dest_cb_path)


    def on_created(self, event):
        """Called when a shard/directory is created in the node directory.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`~watchdog.events.FileSystemEvent`
        """
        super(NodeDirMonitor, self).on_created(event)

        if not self.shardp(event.src_path) and not event.is_directory:
            # the file created can be ignored as it is not a shard or
            # a directory.
            return


        # make note of this file creation; will be used when
        # on_modified is called after this file creatiion.
        self.just_created[event.src_path] = True

        file_cb_path = cb_path(event.src_path, self.config)

        if event.is_directory and (not path.exists(file_cb_path)):
            # means, the directory was created on another computer
            # (also running combox). so, create this directory
            # under the combox directory
            with self.lock:
                self.silo.node_set('file_created', file_cb_path)
                num = self.silo.node_get('file_created', file_cb_path)

                if num == self.num_nodes:
                    os.mkdir(file_cb_path)
                    self.silo.node_rem('file_created', file_cb_path)
        elif (not event.is_directory) and path.exists(file_cb_path):
            # This can either mean the file was create on this
            # computer or if this is a Google Drive node directory and
            # the official Google Drive client is in use this means
            # the file was modified.
            #
            # Google Drive client's behavior when a file (shard) is
            # modified in the Google Drive node directory:
            #
            # - First it deletes the file.
            # - Creates the latest version the file.
            with self.lock:
                num = self.silo.node_get('file_deleted', file_cb_path)
                if num:
                    log_i("Looks like %s was actually modified!" %
                          event.src_path)
                    # This means we're in the Google Drive node
                    # directory and the official Google Drive client
                    # is in use and the file was actually modified on
                    # another computer.
                    self.silo.node_rem('file_deleted', file_cb_path)
                    self.silo.node_set('file_modified', file_cb_path)
                    num = self.silo.node_get('file_modified', file_cb_path)
                    if num == self.num_nodes:
                        log_i("Updating %s ...." % file_cb_path)
                        decrypt_and_glue(file_cb_path, self.config)
                        # update db.
                        self.silo.update(file_cb_path)
                        self.silo.node_rem('file_modified', file_cb_path)
        elif (not event.is_directory) and (not path.exists(file_cb_path)):
            # shard created.

            # means, file was created on another computer (also
            # running combox). so, reconstruct the file and put it
            # in the combox directory.
            with self.lock:
                self.silo.node_set('file_created', file_cb_path)
                num = self.silo.node_get('file_created', file_cb_path)
                if num == self.num_nodes:
                    decrypt_and_glue(file_cb_path, self.config)
                    # update db.
                    self.silo.update(file_cb_path)
                    self.silo.node_rem('file_created', file_cb_path)


    def on_deleted(self, event):
        """Called when a shard/directory is deleted in the node directory.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`~watchdog.events.FileSystemEvent`
        """
        super(NodeDirMonitor, self).on_deleted(event)

        if not self.shardp(event.src_path) and not event.is_directory:
            # the file created can be ignored as it is not a shard or
            # a directory.
            return

        file_cb_path = cb_path(event.src_path, self.config)

        if event.is_directory and path.exists(file_cb_path):
            # This means the directory was deleted on a remote
            # computer.
            with self.lock:
                self.silo.node_set('file_deleted', file_cb_path)
                num = self.silo.node_get('file_deleted', file_cb_path)

                if num == self.num_nodes:
                    # Delete corresponding directory under the combox
                    # directory.
                    if os.listdir(file_cb_path):
                        # There are files under this directory that
                        # are not deleted yet, so we got to delay
                        # deletion :|
                        log_i("Marking %s for later deletion" % file_cb_path)
                        delayed_thread = Timer(15, self.delete_later,
                                               [file_cb_path])
                        delayed_thread.start()
                    else:
                        rm_path(file_cb_path)
                        self.silo.node_rem('file_deleted', file_cb_path)
        elif not event.is_directory and path.exists(file_cb_path):
            log_i("%s must have been deleted on another computer" %
                  event.src_path)
            with self.lock:
                self.silo.node_set('file_deleted', file_cb_path)
                num = self.silo.node_get('file_deleted', file_cb_path)
                # If we are in a Google Drive node directory and
                # the official Google Drive client is in use, at
                # this point we cannot tell if the file was
                # deleted; it can be a file modification or rename
                # or deletion.
                #
                # Therefore, wait for 2secs and then delete the
                # file_cb_path iff the file_cb_path was really
                # removed on the another computer.
                log_i("Marking %s for later deletion" % file_cb_path)
                delayed_thread = Timer(3, self.delete_later,
                                       [file_cb_path])
                delayed_thread.start()


    def on_modified(self, event):
        """Called when a shard/directory is modified in the node directory.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`~watchdog.events.FileSystemEvent`
        """
        super(NodeDirMonitor, self).on_modified(event)

        if not self.shardp(event.src_path) and not event.is_directory:
            # the file created can be ignored as it is not a shard or
            # a directory.
            return

        file_cb_path = cb_path(event.src_path, self.config)

        # get no. shards available
        shards_there = no_of_shards(file_cb_path, self.config)

        if shards_there != self.num_nodes:
            # got to wait for other shards to arrive!
            return

        if event.is_directory:
            # do nothing
            pass
        elif (not event.is_directory):
            # get file size first
            f_size_MiB = path.getsize(event.src_path) / 1048576.0
            log_i('%s modified %f' % (event.src_path, f_size_MiB))

            # introduce delay to prevent multiple "file modified"
            # events from being generated.
            if f_size_MiB >= 30:
                sleep_time = (f_size_MiB / 30.0)
                log_i("waiting on_modified node monitor %f" % sleep_time)
                time.sleep(sleep_time)
                log_i("end waiting on_modified node monitor")
            else:
                time.sleep(1)

            # watchdog's weirdness
            # --------------------
            #
            # On GNU/Linux, when a file is created, watchdog generates
            # a 'file created' and 'file modified' event; we're
            # tracking this behaviour and ignoring the 'file modified'
            # event.
            #
            if (self.just_created.has_key(event.src_path) and
                self.just_created[event.src_path] and
                platform.system() == 'Linux'):
                self.just_created[event.src_path] = False
                log_i("Just created file %s; ignoring on_modified call." % (
                    event.src_path))
                return

            file_content = decrypt_and_glue(file_cb_path,
                                            self.config,
                                            write=False)
            file_content_hash = hash_file(file_cb_path, file_content)

            if self.silo.stale(file_cb_path, file_content_hash) == True:
                log_i("Found %s stale. Updating it..." % file_cb_path)
                # shard modified

                # means, file was modified on another computer (also
                # running combox). so, reconstruct the file and put it
                # in the combox directory.
                with self.lock:
                    self.silo.node_set('file_modified', file_cb_path)
                    num = self.silo.node_get('file_modified', file_cb_path)
                    if num == self.num_nodes:
                        decrypt_and_glue(file_cb_path, self.config)
                        # update db.
                        self.silo.update(file_cb_path)
                        self.silo.node_rem('file_modified', file_cb_path)
            else:
                log_i("Local modification of %s" % file_cb_path)
