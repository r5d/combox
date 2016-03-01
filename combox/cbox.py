# -*- coding: utf-8 -*-
#
#!/usr/bin/env python
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
import time
import yaml

from argparse import ArgumentParser
from os import path
from os.path import expanduser
from sys import exit
from threading import Lock
from watchdog.observers import Observer

from combox.config import config_cb, get_nodedirs
from combox.events import ComboxDirMonitor, NodeDirMonitor
from combox.gui import ComboxConfigDialog
from combox.log import log_i, log_e

## Function adapted from Watchdog's docs:
## http://pythonhosted.org/watchdog/quickstart.html#quickstart

def run_cb(config):
    """Runs combox.

    - Creates an instance of :class:`.ComboxDirMonitor` to monitor the
      combox directory.

    - Creates an instance of :class:`.NodeDirMonitor` for each node
      directory.

    Exits on Ctrt-C.

    :param dict config:
        A dictionary that contains configuration information about
        combox.

    """
    db_lock = Lock()
    monitor_lock = Lock()

    # start combox directory (cd) monitor (cdm)
    combox_dir = path.abspath(config['combox_dir'])
    cd_monitor = ComboxDirMonitor(config, db_lock, monitor_lock)

    cd_observer = Observer()
    cd_observer.schedule(cd_monitor, combox_dir, recursive=True)
    cd_observer.start()

    # start a node directory monitor for each of the node directories.
    node_dirs =  get_nodedirs(config)
    num_nodes =  len(get_nodedirs(config))

    nd_monitors = []
    nd_observers = []

    for node in node_dirs:
        nd_monitor = NodeDirMonitor(config, db_lock,
                                    monitor_lock)
        nd_observer = Observer()
        nd_observer.schedule(nd_monitor, node, recursive=True)
        nd_observer.start()

        nd_monitors.append(nd_monitor)
        nd_observers.append(nd_observer)

    # Make the first node monitor do the housekeeping.
    nd_monitors[0].housekeep()

    log_i("Hit Ctrl-C to quit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cd_observer.stop()
        for i in range(num_nodes):
            nd_observers[i].stop()
            nd_observers[i].join()
    cd_observer.join()

    log_i("combox exiting. Bye!")


def main():
    """Parses args; starts combox configuration if necessary; starts combox.

    """
    parser = ArgumentParser()
    parser.add_argument("-t", "--test",
                        help="Use the combox config file in testing area.",
                        action="store_true")
    parser.add_argument("-nw", "--cli",
                        help="Use CLI interface only",
                        action="store_true")
    args = parser.parse_args()
    if args.test:
        CONFIG_DIR = path.join('tests', 'test-config')
    else:
        CONFIG_DIR = path.join(expanduser("~"),'.combox')

    config_file = path.join(CONFIG_DIR, 'config.yaml')

    log_i(CONFIG_DIR)

    if (not path.exists(CONFIG_DIR) or
        not path.exists(config_file)):
        # combox not configured.
        if not args.cli:
            ComboxConfigDialog("combox configuration", CONFIG_DIR)
        else:
            config_cb(CONFIG_DIR)

    try:
        config = yaml.load(file(config_file, 'r'))
    except (IOError, yaml.YAMLError) as exc:
        log_e("Unable to open configuration file.")
        log_e("Looks like combox is not configured yet. Exiting.")
        exit(1)

    # run combox.
    run_cb(config)


if __name__ == "__main__":
    main()
