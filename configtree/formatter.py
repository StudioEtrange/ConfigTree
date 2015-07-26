import json
from os import linesep
from pkg_resources import iter_entry_points
from collections import Mapping, Sequence
from numbers import Number

from .tree import rarefy
from .compat import unicode, string


def option(name, **kw):
    def decorator(f):
        if not hasattr(f, '__options__'):
            f.__options__ = []
        f.__options__.append((name, kw))
        return f
    return decorator


@option('rare', action='store_true', help='rarefy tree (default: %(default)s)')
@option('sort', action='store_true', help='sort keys (default: %(default)s)')
@option(
    'indent', type=int, default=None, metavar='<indent>',
    help='indent size (default: %(default)s)',
)
def to_json(tree, rare=False, indent=None, sort=False):
    if isinstance(tree, Mapping):
        if rare:
            tree = rarefy(tree)
        else:
            tree = dict(tree)
    return json.dumps(tree, indent=indent, sort_keys=sort)


@option('prefix', default='', metavar='<prefix>', help='key prefix')
@option(
    'seq_sep', default=' ', metavar='<sep>',
    help='sequence item separator (default: space char)'
)
@option('sort', action='store_true', help='sort keys (default: %(default)s)')
@option(
    'capitalize', action='store_true',
    help='capitalize keys (default: %(default)s)',
)
def to_shell(tree, prefix='', seq_sep=' ', sort=False, capitalize=False):

    def convert(value):
        if value is None:
            return "''"
        if isinstance(value, bool):
            return unicode(value).lower()
        if isinstance(value, Number):
            return unicode(value)
        if isinstance(value, Sequence) and not isinstance(value, string):
            return u"'%s'" % seq_sep.join(
                unicode(item).replace("'", "\\'") for item in value
            )
        return u"'%s'" % unicode(value).replace("'", "\\'")

    result = []

    if isinstance(tree, Mapping):
        keys = tree.keys()
        if sort:
            keys = sorted(keys)
        for key in keys:
            value = convert(tree[key])
            key = key.replace(tree._key_sep, '_')
            if capitalize:
                key = key.upper()
            result.append(u'%s%s=%s' % (prefix, key, value))
    else:
        value = convert(tree)
        result.append(u'%s%s' % (prefix, value))

    return linesep.join(result)


map = {}
for entry_point in iter_entry_points('configtree.formatter'):
    map[entry_point.name] = entry_point.load()
