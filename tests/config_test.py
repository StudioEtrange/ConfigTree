import os
from nose import tools


from configtree.config import ConfigTree


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(data_dir, 'data', 'config')


def abspath_test():
    config = ConfigTree()
    config['__loader__.dir'] = data_dir
    path_1 = config.abspath('test')
    path_2 = config.abspath('../test')
    tools.eq_(path_1, os.path.realpath(os.path.join(data_dir, 'test')))
    tools.eq_(path_2, os.path.realpath(os.path.join(data_dir, '../test')))


def include_test():
    config = ConfigTree()
    config['__loader__.dir'] = data_dir
    config.include('.')
    tools.eq_(list(config['__loader__.queue']), [
        os.path.join(data_dir, 'env.json'),
        os.path.join(data_dir, 'settings.json'),
    ])
    config.include('1/env.json')
    tools.eq_(list(config['__loader__.queue']), [
        os.path.join(data_dir, 'env.json'),
        os.path.join(data_dir, 'settings.json'),
        os.path.join(data_dir, '1', 'env.json'),
    ])
    config.include('1')
    tools.eq_(list(config['__loader__.queue']), [
        os.path.join(data_dir, 'env.json'),
        os.path.join(data_dir, 'settings.json'),
        os.path.join(data_dir, '1', 'env.json'),
        os.path.join(data_dir, '1', 'settings.json'),
    ])


def load_test():
    config = ConfigTree()
    config.load(data_dir)
    tools.eq_(config['env.name'], 'Common')
    tools.eq_(config['settings'], {
        'x': 1,
        'y': 1,
        'z': 1,
    })
    config.load('1')
    tools.eq_(config['env.name'], 'Environment 1')
    tools.eq_(config['settings'], {
        'x': 2,
        'y': 1,
        'z': 1,
    })
