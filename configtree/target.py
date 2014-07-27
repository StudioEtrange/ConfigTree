"""
The module provides converters, which output :class:`configtree.tree.Tree`
objects into various formats.  The converters are available via global variable
``map`` in format ``{'format_name': converter}``.  The map is filled on scaning
entry points ``configtree.target``.  So if you want to extend this module,
you can define this entry point in your own application.  The converter map
is used by shell script defined in :mod:`configtree.script` to covert
configuration tree into other formats.

"""

import pkg_resources

from .compat import json, unicode


__all__ = ['map']


def output_json(tree):
    """
    Convert :class:`configtree.tree.Tree` object into JSON fromat:

    ..  code-block:: pycon

        >>> from configtree import Tree
        >>> print(output_json(Tree({'a.b.c': 1})))
        {
            "a.b.c": 1
        }

    """
    return json.dumps(dict(tree), indent=4, sort_keys=True)


def output_bash(tree):
    """
    Convert :class:`configtree.tree.Tree` object into BASH fromat:

    ..  code-block:: pycon

        >>> from configtree import Tree
        >>> print(output_bash(Tree({'a.b.c': 1})))
        A_B_C='1'

    """
    result = []
    for key in sorted(tree.keys()):
        value = unicode(tree[key]).replace("'", "\\'")
        key = key.replace(tree._key_sep, '_').upper()
        result.append("{0}='{1}'".format(key, value))
    return '\n'.join(result)


map = {}
for entry_point in pkg_resources.iter_entry_points('configtree.target'):
    map[entry_point.name] = entry_point.load()
