import os
from nose import tools


from configtree.loader import load


data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')


def load_file_test():
    result = load(os.path.join(data_dir, '00_default', 'settings.json'))
    tools.eq_(result, {
        'x': 1,
        'y': 1,
        'z': 1,
    })


def load_dir_test():
    result = load(data_dir)
    tools.eq_(result, {
        'env.name': 'env_2',
        'env.path': 'data/env_2',
        'x': 2,
        'y': 1,
        'z': 1,
    })


def postprocess_test():
    def postprocess(tree):
        for k in tree:
            if k.endswith('.path'):
                tree[k] = os.path.abspath(tree[k])
    result = load(data_dir, postprocess=postprocess)
    tools.eq_(result, {
        'env.name': 'env_2',
        'env.path': os.path.abspath('data/env_2'),
        'x': 2,
        'y': 1,
        'z': 1,
    })
