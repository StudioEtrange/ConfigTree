import os

from configtree import make_walk


walk = make_walk(env=os.environ.get('ENV_NAME', 'dev'))
