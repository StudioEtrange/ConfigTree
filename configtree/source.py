"""
The module provides loaders from YAML and JSON files, which load data
into :class:`collections.OrderedDict` objects.  The loaders are available
via global variable ``map`` in the format ``{'.ext': loader}``.  The map is
filled on scaning entry points ``configtree.source``.  So if you want
to extend this module, you can define this entry point in your own package.
The loader map is used by :mod:`configtree.loader` module to fill
:class:`configtree.tree.Tree` objects from files.

"""

import pkg_resources

import yaml
from yaml.constructor import ConstructorError

from .compat import OrderedDict, json


__all__ = ['map']


def from_yaml(data):
    """ Loads data from YAML file into :class:`collections.OrderedDict` """
    return yaml.load(data, Loader=OrderedDictYAMLLoader)


def from_json(data):
    """ Loads data from JSON file into :class:`collections.OrderedDict` """
    return json.load(data, object_pairs_hook=OrderedDict)


map = {}
for entry_point in pkg_resources.iter_entry_points('configtree.source'):
    map[entry_point.name] = entry_point.load()


# The following code has been stolen from https://gist.github.com/844388
# Author is Eric Naeseth


class OrderedDictYAMLLoader(yaml.Loader):
    """ A YAML loader that loads mappings into ordered dictionaries """

    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)

        self.add_constructor(
            'tag:yaml.org,2002:map',
            type(self).construct_yaml_map
        )
        self.add_constructor(
            'tag:yaml.org,2002:omap',
            type(self).construct_yaml_map
        )

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:                                                # pragma: nocover
            raise ConstructorError(
                None, None,
                'expected a mapping node, but found %s' % node.id,
                node.start_mark
            )

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:                         # pragma: nocover
                raise ConstructorError(
                    'while constructing a mapping', node.start_mark,
                    'found unacceptable key (%s)' % exc,
                    key_node.start_mark
                )
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping
