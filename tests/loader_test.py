import os
from nose import tools

from configtree import loader
from configtree.tree import flatten


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(data_dir, 'data', 'loader')


def json_test():
    result = loader.load_json(open(os.path.join(data_dir, 'test.json')))
    result = list(flatten(result))
    tools.eq_(result, [
        ('a', 1),
        ('b', 2),
        ('c.x', 1),
        ('c.y', 2),
        ('c.z', 3),
    ])


def yaml_test():
    result = loader.load_yaml(open(os.path.join(data_dir, 'test.yaml')))
    result = list(flatten(result))
    tools.eq_(result, [
        ('a', 1),
        ('b', 2),
        ('c.x', 1),
        ('c.y', 2),
        ('c.z', 3),
    ])


def map_test():
    tools.eq_(loader.map['.yml'], loader.load_yaml)
    tools.eq_(loader.map['.yaml'], loader.load_yaml)
    tools.eq_(loader.map['.json'], loader.load_json)
