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

import logging

def log_config(level, format_):
    """Configures combox logging module.

    Called by all types of log functions in this module.

    :param int level:
        Logging level. Must be any one of the following constants:

            - :const:`logging.CRITICAL`
            - :const:`logging.DEBUG`
            - :const:`logging.ERROR`
            - :const:`logging.FATAL`
            - :const:`logging.INFO`
            - :const:`logging.WARN`
            - :const:`logging.WARNING`
    :param str format_:
          Format string to pass to :func:`logging.basicConfig`
          function.

    """
    logging.basicConfig(level=level,
                        format=format_,
                        datefmt='%Y-%m-%d %H:%M:%S')


def log_i(msg, format_='%(asctime)s - %(message)s'):
    """Function for logging information.

    :param str msg:
        Log message.
    :param str format_:
          Format string to pass to :func:`log_config` function.

    """
    log_config(logging.INFO, format_=format_)
    logging.info(msg)


def log_e(msg, format_='%(asctime)s - %(message)s'):
    """Function for logging errors.

    :param str msg:
        Log message.
    :param str format_:
          Format string to pass to :func:`log_config` function.

    """
    log_config(logging.ERROR, format_=format_)
    logging.error(msg)
