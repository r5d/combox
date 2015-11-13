# combox

Encrypts files and scatters them across storage provided by Google
Drive and Dropbox.

The ideas for this program is based on [`combobox`][1].

Homepage at <https://ricketyspace.net/combox>


[1]: https://bitbucket.org/bgsucodeloverslab/combobox

# etymology

`combox` is a lazy contraction of the word "combo box". `combox` is
pronounced as "combo box".


# canonical repo

    $ git clone git://ricketyspace.net/combox.git


# runs on

 - GNU/Linux
 - OS X

# using combox

## on GNU/Linux

Install `virtualenv` and python dev. package.

On a Debian based distribution, do:

    # aptitude install virtualenv python-dev

## on OS X

First install [Hombrew][brew.sh]:

    $ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

Then do:

    $ brew update
    $ brew doctor

[brew.sh]: http://brew.sh/

Next, install python from Hombrew:

    $ brew install python

This will also install `pip`.

Lastly do:

    $ pip install virtualenv


## set up combox

Get the latest copy of combox:

    $ git clone git://ricketyspace.net/combox.git

Setup virtual environment:

    $ cd combox
    $ virtualenv .

Activate the virtual environment:

    $ source bin/activate

Install combox:

    $ python setup.py install

Run combox:

    $ combox

Always make sure that the virtual environment is activated before
running combox. To activate virtual environment, do:

    $ cd path/to/combox
    $ source bin/activate


## combox on Windows

At the moment, combox is not compatible with Windows. If you can make
combox work on Windows, look at
<https://ricketyspace.net/combox/windows/> for info on setting up the
development environment on Windows.

# license

`combox` is licensed under the
[GNU General Public License version 3 or later][gpl]. See COPYING.

The `combox` logo (`graphics/logo/combox-logo.svg`) is under [Public Domain][pd].

[gpl]: https://gnu.org/licenses/gpl-3.0.txt
[pd]: https://creativecommons.org/publicdomain/zero/1.0/


# contact

siddharth ravikumar <sravik@bgsu.edu> (gpg id: `0x00B252AF`)
