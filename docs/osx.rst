=======
on os x
=======

.. highlight:: bash

First install Hombrew_::

    $ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

.. _Hombrew:  http://brew.sh/

Then do::

    $ brew update
    $ brew doctor

Next, install python from Hombrew_::

    $ brew install python

This will also install ``pip``.

Install ``virtualenv`` from ``pip``::

    $ pip install virtualenv

See :doc:`setup-combox` for setting up combox in ``develop`` mode.
