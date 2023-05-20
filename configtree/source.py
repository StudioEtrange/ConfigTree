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

import ast
import re

__all__ = ["map"]


def from_yaml(data):
    """ Loads data from YAML file into :class:`collections.OrderedDict` """
    return yaml.load(data, Loader=OrderedDictYAMLLoader)


def from_json(data):
    """ Loads data from JSON file into :class:`collections.OrderedDict` """
    return json.load(data, object_pairs_hook=OrderedDict)


map = {}
for entry_point in pkg_resources.iter_entry_points("configtree.source"):
    map[entry_point.name] = entry_point.load()


def get_marked_buffer(start_mark, end_mark):
    if start_mark.buffer is None:
        return None
    start = start_mark.pointer
    while start > 0 and start_mark.buffer[start-1] not in '\0\r\n\x85\u2028\u2029':
        start -= 1
    end = end_mark.pointer
    while end < len(end_mark.buffer) and end_mark.buffer[end] not in '\0\r\n\x85\u2028\u2029':
        end += 1
    return start_mark.buffer[start:end]

tuple_pattern  = re.compile("^(?:\((?:.|\n|\r)*,?(?:.|\n|\r)*\){1}(?: |\n|\r)*$)")
list_pattern  = re.compile("^(?:\[(?:.|\n|\r)*,?(?:.|\n|\r)*\]{1}(?: |\n|\r)*$)")

# The following code has been stolen from https://gist.github.com/844388
# Author is Eric Naeseth


class OrderedDictYAMLLoader(yaml.Loader):
    """ A YAML loader that loads mappings into ordered dictionaries """

    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)

        self.add_constructor("tag:yaml.org,2002:map", type(self).construct_yaml_map)
        self.add_constructor("tag:yaml.org,2002:omap", type(self).construct_yaml_map)

        # support for native python tuple (a, b, ...)
        self.add_constructor(tag="!!!tuple", constructor=type(self).tuple_constructor)
        self.add_implicit_resolver("!!!tuple", tuple_pattern, first=list("("))

        # override sequece as native python list [a, b, ...] to take care of pythons objects inside list
        self.add_constructor('tag:yaml.org,2002:seq', type(self).list_constructor)
        #self.add_constructor('!!!list',type(self).list_constructor)
        #self.add_implicit_resolver('!!!list', list_pattern, first=list("["))

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:  # pragma: nocover
            raise ConstructorError(
                None,
                None,
                "expected a mapping node, but found %s" % node.id,
                node.start_mark,
            )

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:  # pragma: nocover
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found unacceptable key (%s)" % exc,
                    key_node.start_mark,
                )
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

    def tuple_constructor(self, node):
        tuple_string = self.construct_scalar(node)
        # Consider string '(1)' as a tuple with onlye one element. So add by default a coma to force list type (1,)
        try:
            return_value = ast.literal_eval(tuple_string[:-1] + ",)")
        except SyntaxError as ex:
            return_value = ast.literal_eval(tuple_string)
        return return_value

    # TODO : do not work when used with a file
    def list_constructor(self, node):
        buffer = get_marked_buffer(node.start_mark, node.end_mark)
        if list_pattern.match(str(buffer)):  
            data = []
            yield data
            data.extend(ast.literal_eval(buffer))
        else:
            return self.construct_yaml_seq(node)


# import yaml
# yaml.load("[3, 4, [1,1],(5, 3)]", OrderedDictYAMLLoader)
# yaml.load("(2, [3,4, [1,1] ], [5, (10,11)], (7,8) )", OrderedDictYAMLLoader)
# yaml.load("[3, 4, [1,1], (5, 3), ]", OrderedDictYAMLLoader)

# yaml.load(open(file),OrderedDictYAMLLoader)