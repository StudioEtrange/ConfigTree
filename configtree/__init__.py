import logging

from .tree import Tree, flatten, rarefy
from .loader import (
    Loader, Walker, Updater, PostProcessor, Pipeline,
    load, loaderconf, make_walk, make_update,
)


__all__ = [
    'Tree', 'flatten', 'rarefy',
    'Loader', 'Walker', 'Updater', 'PostProcessor', 'Pipeline',
    'load', 'loaderconf', 'make_walk', 'make_update',
]
__version__ = '0.4'
__author__ = 'Dmitry Vakhrushev <self@kr41.net>'
__license__ = 'BSD'


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
