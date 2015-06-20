"""
The module provides converters, which output :class:`configtree.tree.Tree`
objects into various formats.  The converters are available via global variable
``map`` in format ``{'format_name': converter}``.  The map is filled on scaning
entry points ``configtree.conv``.  So if you want to extend this module,
you can define this entry point in your own package.  The converter map
is used by shell script defined in :mod:`configtree.script` to covert
configuration tree into other formats.

"""

from os import linesep
from pkg_resources import iter_entry_points

from .tree import rarefy
from .compat import json, unicode


__all__ = ['map']


def to_json(tree):
    """
    Convert :class:`configtree.tree.Tree` object into JSON fromat:

    ..  code-block:: pycon

        >>> from configtree import Tree
        >>> print(to_json(Tree({'a.b.c': 1})))
        {
            "a.b.c": 1
        }

    """
    return json.dumps(dict(tree), indent=4, sort_keys=True)


def to_rare_json(tree):
    """
    Convert :class:`configtree.tree.Tree` object into JSON fromat:

    ..  code-block:: pycon

        >>> from configtree import Tree
        >>> print(to_rare_json(Tree({'a.b.c': 1})))
        {
            "a": {
                "b": {
                    "c": 1
                }
            }
        }

    """
    return json.dumps(rarefy(tree), indent=4, sort_keys=True)


def to_shell(tree):
    """
    Convert :class:`configtree.tree.Tree` object into shell script fromat:

    ..  code-block:: pycon

        >>> from configtree import Tree
        >>> print(to_shell(Tree({'a.b.c': 1})))
        A_B_C='1'

    """
    result = []
    for key in sorted(tree.keys()):
        value = tree[key]
        if value is None:
            value = ''
        value = unicode(value).replace("'", "\\'")
        key = key.replace(tree._key_sep, '_').upper()
        result.append("{0}='{1}'".format(key, value))
    return linesep.join(result)


map = {}
for entry_point in iter_entry_points('configtree.conv'):
    map[entry_point.name] = entry_point.load()
