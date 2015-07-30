"""
The module provides loaders from YAML and JSON files, which load data
into :class:`collections.OrderedDict` objects.

..  data:: map

    Dictionary that stores map of loaders.  It is filled using
    `entry points`_ named ``configtree.source``.  But can be also modified
    within ``loaderconf.py`` module to add ad hoc loader.

    The map is used by :class:`configtree.loader.Walker` to determine
    supportable files and :class:`configtree.loader.Loader` to load
    data from the files.

.. _entry points: https://pythonhosted.org/setuptools/setuptools.html
                  #dynamic-discovery-of-services-and-plugins

"""

import pkg_resources
import json
from collections import OrderedDict

import yaml
from yaml.constructor import ConstructorError


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
