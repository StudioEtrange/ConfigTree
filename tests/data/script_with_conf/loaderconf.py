import os

from configtree import make_walk


walk = make_walk(env=os.environ.get('ENV_NAME', 'dev'))


def postprocess(tree):
    """ Performs validation of tree """
    for key, value in tree.items():
        if value is None:
            raise ValueError('Required key %s is missing' % key)
