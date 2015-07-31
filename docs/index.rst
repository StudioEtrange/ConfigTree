.. ConfigTree documentation master file, created by
   sphinx-quickstart on Thu May 23 00:23:54 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ConfigTree
==========

Configuration files behave like cancer tumor.  As soon as one is created with
a handful of parameters, it starts to grow.  And in a couple of month it becomes
a huge hardly supportable monster with dozens of parameters, which affects
on different subsystems of the project like metastasis.

The goal of ConfigTree project is to restrain the monster, but without an
overkill for small projects.  It can be used in two ways:

1.  Load and keep configuration within Python code.
2.  Build configuration files using command-line utility and use them within
    non-Python programs.

ConfigTree will be useful for you, if you want to:

*   keep default configuration options and environment-specific ones separated
    (even for complex tree-like structure of environments);
*   keep subsystem settings separated;
*   validate configuration;
*   have templates and automation in your configuration files.

ConfigTree supports out of the box YAML and JSON source files, but it can
be easily :ref:`extended <extending_source>`.  Command-line utility builds
configuration to JSON (condensed or rare) and shell script format, and can be
:ref:`extended <extending_output>` in the same way.


..  toctree::
    :maxdepth: 2

    getting_started
    advanced_usage
    changelog
    migration
    internals/index


Contribution And Bug Reports
----------------------------

The project sources are hosted by BitBucket_ as well, as its bug tracker.
Pull requests, bug reports, and feedback are welcome.

.. _BitBucket: https://bitbucket.org/kr41/configtree


License
-------

The code is licensed under the terms of BSD 2-Clause license. The full text of
the license can be found at the root of the sources.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

