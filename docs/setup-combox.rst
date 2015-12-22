=============
setup combox
=============

.. highlight:: bash

Get the latest copy of combox::

    $ git clone git://ricketyspace.net/combox.git

Setup virtual environment::

    $ cd combox
    $ virtualenv .

Activate the virtual environment::

    $ source bin/activate

Install combox in ``develop`` mode::

    $ python setup.py develop

Always make sure that the virtual environment is activated before
running combox. To activate virtual environment, do::

    $ cd path/to/combox
    $ source bin/activate
