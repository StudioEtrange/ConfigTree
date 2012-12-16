import os
from pkg_resources import EntryPoint
from collections import deque

from .tree import Tree, flatten
from .compat import string
from .loader import load_json, load_yaml


class ProcessingTree(Tree):
    """
    A Processing Tree is sublcass of :class:`Tree` which able to process
    items during update.

    First use case is list merging:

    ..  codeblock-pycon::

        >>> pt = ProcessingTree({'a.b.c': [1, 2, 3]})
        >>> pt['a.b.c#extend'] = [4, 5, 6]
        >>> pt
        ProcessingTree({'a.b.c': [1, 2, 3, 4, 5, 6]})

    Next one is executing expression from string value:

    ..  codeblock-pycon::

        >>> pt = ProcessingTree()
        >>> pt['a.b.c'] = '>>> 1 + 1'
        >>> pt['a.b.c']
        2
        >>> pt['a.b.d'] = ">>> self['a.b.c'] * 2"
        >>> pt['a.b.d']
        4
        >>> pt['a.b.e'] = ">>> branch['d'] + 2"
        >>> pt['a.b.e']
        6

    Update ``namespace`` attribute to extend names available in expression:

    ..  codeblock-pycon::

        >>> from math import floor
        >>> pt.namespace['floor'] = floor
        >>> pt['x'] = '>>> int(floor(3.8))'
        >>> pt['x']
        3

    """

    _method_sep = '#'
    _exp_prefix = '>>> '

    def __init__(self, data=None, namespace=None):
        self.namespace = namespace or {}
        super(ProcessingTree, self).__init__(data)

    def __setitem__(self, key, value):
        if isinstance(value, string) and value.startswith(self._exp_prefix):
            if self._key_sep in key:
                branch_key = key.rsplit(self._key_sep, 1)[0]
                branch = self.branch(branch_key)
            else:
                branch = self
            local = {'self': self, 'branch': branch}
            value = value[len(self._exp_prefix):]
            value = eval(value, self.namespace, local)
        if self._method_sep in key:
            key, method = key.split(self._method_sep)
            getattr(self[key], method)(value)
        else:
            super(ProcessingTree, self).__setitem__(key, value)


class ConfigTree(ProcessingTree):
    """
    A Configuration Tree is a subclass of :class:`ProcessingTree`, which able
    to load its content from files.

    """

    loaders = {
        '.json': load_json,
        '.yaml': load_yaml,
    }

    def load(self, path):
        queue = deque()

        def abspath(relpath):
            if os.path.isabs(relpath):
                return relpath
            curpath = self['__dir__']
            result = os.path.join(curpath, relpath)
            result = os.path.realpath(result)
            return result

        def enqueue(pathes):
            for path in reversed(pathes):
                path = abspath(path)
                if os.path.isfile(path) and \
                   os.path.splitext(path)[1] in self.loaders and \
                   path not in queue:
                    queue.appendleft(path)
                elif os.path.isdir(path):
                    files = []
                    for name in os.listdir(path):
                        subpath = os.path.join(path, name)
                        if os.path.isfile(subpath):
                            files.append(subpath)
                    enqueue(sorted(files))

        global_namespace = self.namespace.copy()
        enqueue([path])
        while queue:
            path = queue.popleft()
            self['__file__'] = path
            self['__dir__'] = os.path.dirname(path)
            ext = os.path.splitext(path)[1]
            with open(path) as f:
                data = self.loaders[ext](f)
                imports = data.pop('__import__', {})
                self.namespace.update((alias, _import(ep))
                                      for alias, ep in imports.items())
                self.update(flatten(data))
                self.namespace = global_namespace
            include = self.pop('__include__', [])
            if isinstance(include, string):
                include = [include]
            enqueue(include)
            del self['__file__'], self['__dir__']


def _import(ep):
    if ep not in _import.cache:
        _import.cache[ep] = EntryPoint.parse('x={0}'.format(ep)).load(False)
    return _import.cache
_import.cache = {}
