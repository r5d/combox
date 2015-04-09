<!-- -*- mode: markdown; -*- -->

# combox

Encrypts files and scatters them across storage provided by
proprietary online file storage providers like Google Drive, Dropbox,
etc.

The ideas for this program is based on [`combobox`][1].

[1]: https://bitbucket.org/bgsucodeloverslab/combobox

Criticism is welcome here.

# etymology

`combox` is a lazy contraction of the word "combo box". `combox` is
pronounced as "combo box".

# status

Core functionality is being written at the moment. See `TODO.org`.

# requirements

* setuptools v5.5.x
* virtualenv v1.9.x or later
* python v2.7.x

# dependencies

* argparse v1.2.x or later
* nose v1.3.x
* pycrypto v2.6.1
* pickledb v0.3
* PyYAML v3.x
* watchdog v0.8.2

# platform

At the moment `combox` is written and tested on a GNU/Linux based
operating system.

# setting up the environment

Install `virtualenv` and python's `setuptools` packages.

From the same directory as this README file, do:

    $ virtualenv .

Activate the virtual environment:

    $ source bin/activate

Install dependencies by simply installing combox:

    $ python setup.py install

# running tests

    $ nosetests -s

# license

The source code of `combox` is licensed under the [GNU General Public
License version 3 or later][gpl]. See COPYING.

The `combox` logo (`graphics/logo/combox-logo.svg`) is under [Public Domain][pd].

[gpl]: https://gnu.org/licenses/gpl-3.0.txt
[pd]: https://creativecommons.org/publicdomain/zero/1.0/

# canonical repo

    $ git clone http://rsiddharth.ninth.su/git/cb.git

# contact

siddharth ravikumar <sravik@bgsu.edu> (gpg id: `0x00B252AF`)
