"""
The module provides loaders from YAML and JSON files, which load data
into :class:`OrderedDict` objects.

"""

import yaml
from yaml.constructor import ConstructorError

from .compat import OrderedDict, json


__all__ = ['load_yaml', 'load_json']


def load_yaml(data):
    """ Load data from YAML file into ``OrderedDict`` """
    return yaml.load(data, Loader=OrderedDictYAMLLoader)


def load_json(data):
    """ Load data from JSON file into ``OrderedDict`` """
    return json.load(data, object_pairs_hook=OrderedDict)


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
        else:
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
            except TypeError as exc:
                raise ConstructorError(
                    'while constructing a mapping', node.start_mark,
                    'found unacceptable key (%s)' % exc,
                    key_node.start_mark
                )
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping
