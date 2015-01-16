#!/usr/bin/env python
#
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

import os
import time
import yaml

from argparse import ArgumentParser
from os import path
from sys import exit
from watchdog.observers import Observer

from combox.config import config_cb
from combox.events import ComboxEventHandler


## Function adapted from Watchdog's docs:
## http://pythonhosted.org/watchdog/quickstart.html#quickstart

def run_cb(config):
    """
    Runs combox.
    """
    c_path = path.abspath(config['combox_dir'])
    event_handler = ComboxEventHandler(config)

    observer = Observer()
    observer.schedule(event_handler, c_path, recursive=True)
    observer.start()
    print "Hit Ctrl-C to quit."
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("-t", "--test",
                        help="Use the combox config file in testing area.",
                        action="store_true")
    args = parser.parse_args()
    if args.test:
        CONFIG_DIR = path.join('tests', 'test-config')
    else:
        CONFIG_DIR = path.join(os.getenv('HOME'),'.combox/')

    config_file = path.join(CONFIG_DIR, 'config.yaml')

    print CONFIG_DIR

    if not path.exists(CONFIG_DIR):
        # combox not configured.
        config_cb(CONFIG_DIR)
    try:
        config = yaml.load(file(config_file, 'r'))
    except yaml.YAMLError, exc:
        print "Error opening configuration file:", exc
        exit(1)

    # run combox.
    run_cb(config)
