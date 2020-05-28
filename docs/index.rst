.. ConfigTree documentation master file, created by
   sphinx-quickstart on Thu May 23 00:23:54 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ConfigTree
==========

Configuration files behave like cancer tumor.  As soon as one is created with
a handful of parameters, it starts to grow.  And in a couple of month it becomes
huge hardly supportable monster with dozens of parameters, which affects
on different subsystems of the project like metastasis.

The goal of ConfigTree project is to restrain the monster, but without
overkill for small projects.  It can be used in Python programs as well as
in programs written in :ref:`other languages <ctdump>`.

ConfigTree will be useful for you, if you want to:

*   keep default configuration options and environment-specific ones separated;
*   fine-tune files to load for each environment;
*   validate configuration;
*   have templates and automation in your configuration files.

ConfigTree supports out of the box YAML and JSON source files with some
:ref:`syntactic sugar <updater>`.  And the support of other formats can be
easily :ref:`added <source>`.  :ref:`Command-line utility <ctdump>` builds
configuration into JSON and shell script formats, and can be :ref:`extended <formatter>`
in the same way.


..  toctree::
    :maxdepth: 2

    getting_started
    advanced_usage
    changelog
    migration
    internals/index


Contribution And Bug Reports
----------------------------

The project sources are hosted by GitHub_ as well, as its bug tracker.
Pull requests, bug reports, and feedback are welcome.

.. _GitHub: https://github.com/Cottonwood-Technology/ConfigTree


License
-------

The code is licensed under the terms of BSD 2-Clause license. The full text of
the license can be found at the root of the sources.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

