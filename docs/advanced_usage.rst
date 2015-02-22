Advanced Usage
==============


Loading Overview
----------------

The loading of configuration is done by :func:`configtree.loader.load` function.
The function accepts five arguments:

*   ``path``---path to configuration directory;
*   ``walk``---function that controls loading order of files, see factory
    :func:`configtree.loader.make_walk` for details;
*   ``update``---function that adds syntax sugar to configuration, see factory
    :func:`configtree.loader.make_update` for details;
*   ``postprocess``---function that performs post-processing of result tree
    object;
*   ``tree``---initial tree object, see :class:`configtree.tree.Tree` for
    details.

When you use ``configtree`` command-line utility, it will populate these
arguments from ``loaderconf.py`` file.  If you use ConfigTree within Python
program, you can use :func:`configtree.loader.load` function directly.  See
its description for detailed information.

Each file is loaded into :class:`collections.OrderedDict` to preserve order
of settings.  So that, templates and expressions provided by ``update`` function
can be used.

Nested mapping objects are flatten by :func:`configtree.tree.flatten`,
i.e. tree hierarchy of mappings will be converted to single mapping using
dot-separated keys:

..  doctest::

    >>> from configtree import flatten
    >>> dict(flatten({'a': {'x': 1, 'y': 2}})) == {'a.x': 1, 'a.y': 2}
    True

So that, following two examples are equal:

..  code-block:: yaml

    # Using nested mapping is equal to...
    a:
        x: 1
        y: 2

    # ...using dot-separated keys
    a.x: 1
    a.y: 2


Extending Supported Source Formats
----------------------------------

Loading file itself is done by loaders from :mod:`configtree.source` module.
Out of the box YAML and JSON loaders are available.  If you want to add
support of another format, you should implement function that accepts
file object and returns :class:`collections.OrderedDict`.  For instance:

..  code-block:: python

    # For compatibility with Python 2.6
    from configtree.compat import OrderedDict

    def from_xml(data):
        # Do something with ``data`` file
        return OrderedDict(...)

If you want to distribute this function as ConfigTree plugin, use entry points
mechanism, i.e. add to your ``setup.py`` file something like this:

..  code-block:: python

    entry_points="""\
    [configtree.source]
    .xml = configtree_xml:from_xml
    """

If you want to use it just in your own project, you can place this function
into ``loaderconf.py`` file and add it to the ``source.map`` manually:

..  code-block:: python

    from configtree import source

    source.map['.xml'] = from_xml


Extending Supported Output Formats
----------------------------------

Outputting is done by converters from :mod:`configtree.conv` module.  Out of
the box JSON and Shell-script formats are available.  If you want to add
support of another format, you should implement function that accepts
:class:`configtree.tree.Tree` object and returns string.  For instance:

    def to_xml(tree):
        pass

If you want to distribute this function as ConfigTree plugin, use entry points
mechanism, i.e. add to your ``setup.py`` file something like this:

..  code-block:: python

    entry_points="""\
    [configtree.conv]
    xml = configtree_xml:to_xml
    """

If you want to use it just in your own project, you can place this function
into ``loaderconf.py`` file and add it to the ``conv.map`` manually:

..  code-block:: python

    from configtree import conv

    conv.map['xml'] = to_xml

It will work.  However, format will not be shown by ``configtree`` help
message, because this message is build before loading ``loaderconf.py`` file.
