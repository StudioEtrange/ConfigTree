import logging

from .tree import ITree, Tree, flatten, rarefy
from .loader import (
    Loader, Walker, Updater, PostProcessor, Pipeline,
    load, loaderconf, make_walk, make_update,
)


__all__ = [
    'ITree', 'Tree', 'flatten', 'rarefy',
    'Loader', 'Walker', 'Updater', 'PostProcessor', 'Pipeline',
    'load', 'loaderconf', 'make_walk', 'make_update',
]
__version__ = '0.5.1'
__author__ = 'Dmitry Vakhrushev <self@kr41.net>'
__license__ = 'BSD'


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
