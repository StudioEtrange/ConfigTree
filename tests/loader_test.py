import os
from nose import tools

from configtree.loader import load_json, load_yaml
from configtree.tree import flatten


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(data_dir, 'data', 'loader')


def json_test():
    result = load_json(open(os.path.join(data_dir, 'test.json')))
    result = list(flatten(result))
    tools.eq_(result, [
        ('a', 1),
        ('b', 2),
        ('c.x', 1),
        ('c.y', 2),
        ('c.z', 3),
    ])


def yaml_test():
    result = load_yaml(open(os.path.join(data_dir, 'test.yaml')))
    result = list(flatten(result))
    tools.eq_(result, [
        ('a', 1),
        ('b', 2),
        ('c.x', 1),
        ('c.y', 2),
        ('c.z', 3),
    ])
