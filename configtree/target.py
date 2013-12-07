"""
The module provides converters, which output :class:`Tree` objects into
various formats.

"""

import pkg_resources

from .compat import json


__all__ = ['map']


def output_json(tree):
    """ Convert :class:`Tree` object into JSON fromat """
    return json.dumps(dict(tree), indent=4)


def output_bash(tree):
    """ Convert :class:`Tree` object into BASH fromat """
    result = []
    for key, value in tree.items():
        key = key.replace('.', '_').upper()
        result.append('export {0}={1}'.format(key, value))
    return '\n'.join(result)


map = {}
for entry_point in pkg_resources.iter_entry_points('configtree.target'):
    map[entry_point.name] = entry_point.load()
