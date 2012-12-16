import os
import pkg_resources
from collections import deque

from .core import ProcessingTree, flatten


parsers = {}
for entry in pkg_resources.iter_entry_points('configtree.parsers'):
    try:
        parsers[entry.name] = entry.load()
    except ImportError as e:
        pass


class ConfigTree(ProcessingTree):
    """
    A Configuration Tree is a subclass of :class:`ProcessingTree`, which able
    to load its content from files.

    """

    def load(self, path):
        self.include(path)
        queue = self['__loader__.queue']
        while queue:
            path = queue.popleft()
            self['__loader__.dir'] = os.path.dirname(path)
            ext = os.path.splitext(path)[1]
            with open(path) as f:
                data = parsers[ext](f)
                self.update(flatten(data))
            include = self['__loader__'].pop('include', [])
            self.include(*include)

    def include(self, *pathes):
        queue = self.setdefault('__loader__.queue', deque())
        for path in pathes:
            path = self.abspath(path)
            if os.path.isfile(path) and \
               os.path.splitext(path)[1] in parsers and \
               path not in queue:
                queue.append(path)
            elif os.path.isdir(path):
                files = []
                for name in os.listdir(path):
                    subpath = os.path.join(path, name)
                    if os.path.isfile(subpath):
                        files.append(subpath)
                self.include(*sorted(files))

    def abspath(self, relpath):
        curpath = self.get('__loader__.dir', '.')
        result = os.path.join(curpath, relpath)
        result = os.path.realpath(result)
        return result
