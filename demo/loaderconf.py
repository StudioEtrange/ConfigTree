import os

from configtree import make_walk, make_update


update = make_update(namespace={'os': os})
walk = make_walk(env=os.environ['ENV_NAME'])


def postprocess(tree):
    for key, value in tree.items():
        if value is None:
            raise ValueError('Missing required value "%s"' % key)
