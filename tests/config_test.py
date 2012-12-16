import os
from nose import tools


from configtree.config import ConfigTree


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(data_dir, 'data', 'config')

config = ConfigTree()


def load_dir_test():
    config.load(data_dir)
    tools.eq_(config, {
        'env.name': 'Common',
        'settings.x': 1,
        'settings.y': 1,
        'settings.z': 1,
    })


def load_file_with_string_include_test():
    config.load(os.path.join(data_dir, '1', 'env.json'))
    tools.eq_(config, {
        'env.name': 'Environment 1',
        'settings.x': 2,
        'settings.y': 1,
        'settings.z': 1,
    })


def load_file_with_list_include_test():
    config.load(os.path.join(data_dir, '2', 'env.json'))
    tools.eq_(config, {
        'env.name': 'Environment 2',
        'settings.x': 2,
        'settings.y': 3,
        'settings.z': 3,
    })
