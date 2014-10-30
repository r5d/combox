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

from os import path

from utils.file import split_file, glue_file, write_file

### Test to split, glue and create a copy of the image file from the
### glued image file.
f = path.abspath('tests/files/the-red-star.jpg')
f_copy = path.abspath('tests/files/the-red-star-copy.jpg')
f_parts = split_file(f, 3)
filecontent = glue_file(f_parts)
write_file(f_copy, filecontent)
