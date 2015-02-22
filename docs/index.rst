.. ConfigTree documentation master file, created by
   sphinx-quickstart on Thu May 23 00:23:54 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ConfigTree's documentation!
======================================

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

*   keep default configuration options and environment-specific separated
    (even for complex tree-like structure of environments);
*   keep subsystem settings separated;
*   validate configuration;
*   have templates and automation in your configuration files.

ConfigTree supports out of the box YAML and JSON source files, but it can
be easily extended.  Command-line utility builds configuration to JSON and
shell script format, and can be extended in the same way.


.. toctree::
   :maxdepth: 2

   getting_started
   advanced_usage
   internals

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

