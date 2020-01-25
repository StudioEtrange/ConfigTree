"""
The module provides formatters of :class:`configtree.tree.Tree` objects

..  data:: map

    Dictionary that stores map of formatters.  It is filled using
    `entry points`_ named ``configtree.formatter``.  But can be also modified
    within ``loaderconf.py`` module to add ad hoc formatter.
    See :mod:`configtree.loader`.

    The map is used by script :func:`configtree.script.ctdump` to load
    available formatters and print result.


.. _entry points: https://pythonhosted.org/setuptools/setuptools.html
                  #dynamic-discovery-of-services-and-plugins

"""

import json
from os import linesep
from pkg_resources import iter_entry_points
from numbers import Number

from .tree import rarefy
from .compat.types import string, chars
from .compat.colabc import Mapping, Sequence


def option(name, **kw):
    """
    Decorator that adds ``__options__`` list to formatter and puts passed
    parameters into the list as a tuple ``(name, kw)``.

    The ``__options__`` list is used by script :func:`configtree.script.ctdump`
    to include options into its argument parser.  See :mod:`argparse`.

    :param str name: Option name
    :param dict kw: Option parameters that are passed into
                    :meth:`argparse.ArgumentParser.add_argument`

    """

    def decorator(f):
        if not hasattr(f, "__options__"):
            f.__options__ = []
        f.__options__.append((name, kw))
        return f

    return decorator


@option("rare", action="store_true", help="rarefy tree (default: %(default)s)")
@option("sort", action="store_true", help="sort keys (default: %(default)s)")
@option(
    "indent",
    type=int,
    default=None,
    metavar="<indent>",
    help="indent size (default: %(default)s)",
)
def to_json(tree, rare=False, indent=None, sort=False):
    """
    Format ``tree`` into JSON

    :param Tree tree: Tree object to format
    :param bool rare: Use :func:`configtree.tree.rarefy` on tree before format
    :param int indent: Indent size
    :param bool sort: Sort keys

    Examples:

    ..  code-block:: pycon

        >>> from configtree import Tree

        >>> tree = Tree({'a.x': "Foo", 'a.y': "Bar"})
        >>> result = to_json(tree, indent=4, sort=True)
        >>> print(result)       # doctest: +NORMALIZE_WHITESPACE
        {
            "a.x": "Foo",
            "a.y": "Bar"
        }
        >>> result = to_json(tree, rare=True, indent=4, sort=True)
        >>> print(result)       # doctest: +NORMALIZE_WHITESPACE
        {
            "a": {
                "x": "Foo",
                "y": "Bar"
            }
        }

    """
    if isinstance(tree, Mapping):
        if rare:
            tree = rarefy(tree)
        else:
            tree = dict(tree)
    return json.dumps(tree, indent=indent, sort_keys=sort)


@option(
    "prefix", default="", metavar="<prefix>", help="key prefix (default: empty string)"
)
@option(
    "seq_sep",
    default=" ",
    metavar="<sep>",
    help="sequence items separator (default: space char)",
)
@option("sort", action="store_true", help="sort keys (default: %(default)s)")
@option(
    "capitalize", action="store_true", help="capitalize keys (default: %(default)s)"
)
def to_shell(tree, prefix="", seq_sep=" ", sort=False, capitalize=False):
    """
    Format ``tree`` into shell (Bash) expression format

    :param Tree tree: Tree object to format
    :param bool prefix: Key prefix
    :param str seq_sep: Sequence items separator
    :param bool sort: Sort keys
    :param bool capitalize: Capitalize keys

    Examples:

    ..  code-block:: pycon

        >>> from configtree import Tree

        >>> tree = Tree({'a.x': "Foo", 'a.y': "Bar"})
        >>> result = to_shell(tree, prefix='local ', sort=True)
        >>> print(result)       # doctest: +NORMALIZE_WHITESPACE
        local a_x='Foo'
        local a_y='Bar'
        >>> result = to_shell(tree, sort=True, capitalize=True)
        >>> print(result)       # doctest: +NORMALIZE_WHITESPACE
        A_X='Foo'
        A_Y='Bar'

        >>> tree = Tree({'list': [1, 2, 3]})
        >>> result = to_shell(tree)
        >>> print(result)       # doctest: +NORMALIZE_WHITESPACE
        list='1 2 3'
        >>> result = to_shell(tree, seq_sep=':')
        >>> print(result)       # doctest: +NORMALIZE_WHITESPACE
        list='1:2:3'

    """

    def convert(value):
        if value is None:
            return "''"
        if isinstance(value, bool):
            return string(value).lower()
        if isinstance(value, Number):
            return string(value)
        if isinstance(value, Sequence) and not isinstance(value, chars):
            return u"'%s'" % seq_sep.join(
                string(item).replace("'", "\\'") for item in value
            )
        return u"'%s'" % string(value).replace("'", "\\'")

    result = []

    if isinstance(tree, Mapping):
        keys = tree.keys()
        if sort:
            keys = sorted(keys)
        for key in keys:
            value = convert(tree[key])
            key = key.replace(tree._key_sep, "_")
            if capitalize:
                key = key.upper()
            result.append(u"%s%s=%s" % (prefix, key, value))
    else:
        value = convert(tree)
        result.append(u"%s%s" % (prefix, value))

    return linesep.join(result)


map = {}
for entry_point in iter_entry_points("configtree.formatter"):
    map[entry_point.name] = entry_point.load()
