<!-- -*- mode: markdown; -*- -->

# combox

Splits and encrypts files and scatters them to directories from which
files are slurped into surveillance nodes like Google Docs, Dropbox,
etc.

The ideas for this program is based on [`combobox`][1].

[1]: https://bitbucket.org/bgsucodeloverslab/combobox

# etymology

`combox` is a lazy contraction of the word "combo box". `combox` is
pronounced as "combo box".

# status

Core functionality is being written at the moment.

# requirements

* setuptools v5.5.x
* virtualenv v1.9.x or later
* python v2.7.x
* PyYAML v3.x
* nose v1.3.x
* watchdog v0.8.2
* pycrypto v2.6.1

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

    $ nosetests

# license

`combox` is licensed under the GNU General Public License version 3 or
later. See COPYING.

# contact

siddharth ravikumar <sravik@bgsu.edu> (`gpg id: 0x00B252AF`)
