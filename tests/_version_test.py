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

import mock

import combox._version

from nose.tools import *

from combox._version import get_version


def test_get_version():
    """
    Testing combox._version.get_version()
    """
    with mock.patch('combox._version.__version__', '0.9'), \
        mock.patch('combox._version.__release__', '.423'):

        version = "%s.%s" % (combox._version.__version__,
                             combox._version.__release__)
        assert get_version()  == version
