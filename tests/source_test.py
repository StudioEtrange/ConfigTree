import os
from nose import tools

from configtree import source
from configtree.tree import flatten


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(data_dir, "data", "source")


def json_test():
    with open(os.path.join(data_dir, "test.json")) as f:
        result = source.from_json(f)
        result = list(flatten(result))
        tools.eq_(result, [("a", 1), ("b", 2), ("c.x", 1), ("c.y", 2), ("c.z", 3)])


def yaml_test():
    with open(os.path.join(data_dir, "test.yaml")) as f:
        result = source.from_yaml(f)
        result = list(flatten(result))
        tools.eq_(result, [("a", 1), ("b", 2), ("c.x", 1), ("c.y", 2), ("c.z", 3)])


def map_test():
    tools.eq_(source.map[".yml"], source.from_yaml)
    tools.eq_(source.map[".yaml"], source.from_yaml)
    tools.eq_(source.map[".json"], source.from_json)
