import math
import os
from nose import tools

from configtree.loader import load, make_walk, make_update
from configtree.tree import Tree


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(data_dir, 'data', 'loader')


def walk_test():
    walk = make_walk()
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    tools.eq_(files, [
        os.path.join('default', 'a.json'),
        os.path.join('default', 'b.yaml'),
        os.path.join('default', 'subsystem', 'a.yaml'),
        os.path.join('default', 'subsystem', 'b.yaml'),
    ])

    walk = make_walk(env='y')
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    tools.eq_(files, [
        os.path.join('default', 'a.json'),
        os.path.join('default', 'b.yaml'),
        os.path.join('default', 'subsystem', 'a.yaml'),
        os.path.join('default', 'subsystem', 'b.yaml'),
        'env-y.yaml',
    ])

    walk = make_walk(env='x')
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    tools.eq_(files, [
        os.path.join('default', 'a.json'),
        os.path.join('default', 'b.yaml'),
        os.path.join('default', 'subsystem', 'a.yaml'),
        os.path.join('default', 'subsystem', 'b.yaml'),
        os.path.join('env-x', 'a.yaml'),
    ])

    walk = make_walk(env='x.xx')
    files = [os.path.relpath(f, data_dir) for f in walk(data_dir)]
    tools.eq_(files, [
        os.path.join('default', 'a.json'),
        os.path.join('default', 'b.yaml'),
        os.path.join('default', 'subsystem', 'a.yaml'),
        os.path.join('default', 'subsystem', 'b.yaml'),
        os.path.join('env-x', 'a.yaml'),
        os.path.join('env-x', 'env-xx', 'b.yaml'),
    ])


def update_test():
    tree = Tree({'a.b.x': 1})

    update = make_update()
    update(tree, 'a.b.y', 2)
    tools.eq_(tree['a.b.y'], 2)

    update(tree, 'a.b.z', '>>> self["a.b.x"] + branch["y"]')
    tools.eq_(tree['a.b.z'], 3)

    update(tree, 'a.b.l?', [])
    tools.eq_(tree['a.b.l'], [])

    update(tree, 'a.b.l?', [1, 2, 3])
    tools.eq_(tree['a.b.l'], [])

    update(tree, 'a.b.l#extend', [4, 5, 6])
    tools.eq_(tree['a.b.l'], [4, 5, 6])

    update(tree, 'a.b.c', '$>> x = {self[a.b.x]}, y = {branch[y]}')
    tools.eq_(tree['a.b.c'], 'x = 1, y = 2')

    update = make_update(namespace={'floor': math.floor})
    update(tree, 'z', '>>> int(floor(3.8))')
    tools.eq_(tree['z'], 3)


def load_test():
    update = make_update(namespace={'floor': math.floor})
    result = load(data_dir, update=update)
    tools.eq_(result, {
        'a.x': 1,
        'a.y': 2,
        'b.x': 10,
        'b.y': 20,
        'subsystem.a.x': 101,
        'subsystem.a.y': 102,
        'subsystem.b.x': 110,
        'subsystem.b.y': 120,
    })

    walk = make_walk(env='y')
    result = load(data_dir, walk=walk, update=update)
    tools.eq_(result, {
        'a.x': 1,
        'a.y': 2,
        'b.x': 10,
        'b.y': 20,
        'subsystem.a.x': 101,
        'subsystem.a.y': 102,
        'subsystem.b.x': 110,
        'subsystem.b.y': 120,
        'a.b.x': 1,
        'a.b.y': 2,
        'a.b.z': 3,
        'a.b.c': 'x = 1, y = 2',
        'a.b.l': [4, 5, 6],
        'z': 3,
        'path': os.path.join(data_dir, 'somepath'),
        'here': os.path.join(data_dir, 'env-y.yaml'),
    })
