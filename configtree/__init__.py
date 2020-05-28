import logging

from .tree import ITree, Tree, flatten, rarefy
from .loader import Loader, Walker, Updater, PostProcessor, Pipeline


__all__ = [
    "ITree",
    "Tree",
    "flatten",
    "rarefy",
    "Loader",
    "Walker",
    "Updater",
    "PostProcessor",
    "Pipeline",
]
__version__ = "0.6"
__author__ = "Cottonwood Technology <info@cottonwood.tech>"
__license__ = "BSD"


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
