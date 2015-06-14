
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

The full documentation is available at `Read the Docs`_.


.. _Read the Docs: http://configtree.readthedocs.org/en/latest/
