==========
on windows
==========

.. highlight:: powershell

At the moment, ``combox`` is not compatible with Windows. The following
sections describe how to set up the development environment on
Windows.


setup python, pip and virtualenv
--------------------------------

Install python v2.7.x first: `python.org/downloads/windows`__

.. _pywindows: https://www.python.org/downloads/windows
.. __: pywindows_

Add python to ``PATH``:

.. code-block:: none

   %PATH%;C:\Python27

Make sure python works from Windows Powershell

Get a copy of `get-pip.py`_.

.. _get-pip.py: https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py

From Windows Powershell, ``cd`` to the directory containing
``get-pip.py`` file and do::

  python get-pip.y

That should install ``pip`` and ``setuptools``.

Next, add pip to ``PATH``:

.. code-block:: none

    %PATH%;C:\Python27;C:\Python27\Scripts

Make sure ``pip`` works from Windows Powershell by doing::

  pip --version

Lastly, install ``virtualenv``::

  pip install virtualenv


install git
-----------

Get a copy of ``git`` from `git-scm.com/download/win`__

.. _gitwin: http://git-scm.com/download/win
.. __: gitwin_

In the "Adjusting your PATH environment" screen in the ``git``
installation wizard, choose the "Use Git from the Windows Command
Prompt"

Make sure ``git`` works from Windows Powershell by doing::

  git --version


setup combox
------------


install v. c++ compiler
=======================

From `aka.ms/vcpython27`__ (this is required for installing
``pycrypto`` package from ``pip``).

.. _vcpython27: http://aka.ms/vcpython27
.. __: vcpython27_


setup combox
==============

From the Windows Powershell, do::

  git clone git://ricketyspace.net/combox.git


setup virtual environment
.........................

``cd`` to the ``combox`` directory and do::

  virtualenv .


activate virtual environment
............................

``cd`` to the ``combox`` directory and do::

  .\Scripts\activate


install combox
..............

in ``develop`` mode::

  python setup.py develop
