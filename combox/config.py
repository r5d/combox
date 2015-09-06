
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

##################################################
## YAML Config format
##################################################
##
## combox_dir: path/to/combox/
##
## topsecret: dba0079f1cb3a3b56e102dd5e04fa2af
##
## nodes_info:
##  node_name:
##      path: path/to/shard1/dir/
##      size: 1000 # in MB
##      available: 500 # in MB
##  node name:
##      path: path/to/shard2/dir/
##      size: 2000
##      available: 1500
##  node name:
##      path: path/to/shard3/dir
##      size: 3000
##      available: 1500
##
##################################################

import os
import yaml
import getpass
import hashlib
import sys
import stat

from os import path
from os.path import expanduser

def get_secret():
    "Gets the pass phrase from std. input."
    return getpass.getpass('passphrase: ')


def get_stdin(prompt):
    "Gets a string from std. input."

    prompt = "%s: "  % (prompt)

    return raw_input(prompt)


def config_cb(config_dir = path.join(expanduser("~"), '.combox'),
              pass_func = get_secret,
              input_func = get_stdin,
              write=True):
    """
    Configure combox.
    """

    if not path.exists(config_dir):
        # Create combox dir.
        os.mkdir(config_dir, 0700)
    config_file_path = path.join(config_dir, 'config.yaml')
    config_info = {}

    config_info['combox_name'] = input_func('name of this combox')
    config_info['combox_dir'] = path.abspath(expanduser(input_func('path to combox directory')))

    silo_help_txt = 'silo directory (default: %s)' % (config_dir)
    silo_dir = expanduser(input_func(silo_help_txt))

    if silo_dir:
        config_info['silo_dir'] = path.abspath(silo_dir)
    else:
        config_info['silo_dir'] = path.abspath(config_dir)

    config_info['topsecret'] = pass_func()

    no_nodes = int(input_func('number of nodes'))
    nodes = {}
    for i in range(no_nodes):
        node_name = input_func('node %d name' % i)
        nodes[node_name] = {}
        nodes[node_name]['path'] = path.abspath(expanduser(input_func('node %d path' % i)))
        nodes[node_name]['size'] = input_func('node %d size (in mega bytes)' % i)
        nodes[node_name]['available'] = nodes[node_name]['size']

        # create node path, if it doesn't exists yet.
        if not path.exists(nodes[node_name]['path']):
            os.makedirs(nodes[node_name]['path'])

    config_info['nodes_info'] = nodes
    if write:
        config_file = open(config_file_path, 'w')
        yaml.dump(config_info, config_file, default_flow_style=False)
        os.chmod(config_file_path,stat.S_IRUSR|stat.S_IWUSR)
        return config_info
    else:
        return config_info


def get_nodedirs(config):
    """
    Returns the node path to directories as a list.

    config: a dictionary which has the combox configuration
    """
    nodes = []

    for node in config['nodes_info'].itervalues():
        node_path = path.abspath(node['path'])
        nodes.append(node_path)

    return sorted(nodes)
