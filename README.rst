===============================
proj
===============================

.. image:: https://badge.fury.io/py/proj.png
    :target: http://badge.fury.io/py/proj

.. image:: https://travis-ci.org/larsyencken/proj.png?branch=master
        :target: https://travis-ci.org/larsyencken/proj

.. image:: https://pypip.in/d/proj/badge.png
        :target: https://pypi.python.org/pypi/proj


A command-line folder manager for archiving and restoring a long-term set of projects.

* Free software: BSD license
* Documentation: https://proj.readthedocs.org.

``proj`` assumes the following working setup:

- You have a directory of active projects that you're working on (e.g. ~/Projects)
- You have a directory of inactive projects, your archive (e.g. ~/Archive)

Given this setup, ``proj`` helps you add and remove projects from your archive, and keeps your archive organised in ``<year>/<quarter>`` subfolders, based on when each project was last worked on.

Installation
------------

Install the package with pip:

.. code:: console

    pip install proj

Then, tell ``proj`` where your archive directory is, by creating a ``~/.proj.yml`` file

.. code::

    archive_dir: _archive

You can enable compression for archives by adding more directives to the YAML file:

.. code::

    compression: true
    compression_format: bztar

The supported formats are: ``tar``, ``gztar``, ``bztar`` and ``zip``.

Usage
-----

Use proj to get rid of clutter in your main directory of projects by archiving ones that aren't being worked on. Proj will detect when you last made a change and file it accordingly.

.. code:: console

    $ ls
    cocktails-that-are-blue   news-for-llamas   old-crusty-project
    $ proj archive old-crusty-project
    old-crusty-project -> /Users/lars/Archive/2012/q3/old-crusty-project
    $ ls
    cocktails-that-are-blue   news-for-llamas
    $ proj list
    2012/q3/old-crusty-project

Now we've archived this project, but we can restore it at any time.

.. code:: console

    $ proj restore old-crusty-project
    /Users/lars/Archive/2012/q3/old-crusty-project -> old-crusty-project
    $ ls
    cocktails-that-are-blue   news-for-llamas   old-crusty-project

Features
--------

* ``proj archive``: archive a project to an appropriate directory
* ``proj restore``: restore a project from the archive
* ``proj list``: search the archive for a project
