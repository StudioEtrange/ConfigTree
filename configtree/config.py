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

    Update ``__namespace__`` branch to extend names available in expression:

    ..  codeblock-pycon::

        >>> from math import floor
        >>> pt['__namespace__.floor'] = floor
        >>> pt['x'] = '>>> int(floor(3.8))'
        >>> pt['x']
        3

    Any string passed to ``__namespace__`` branch will be treated as name
    to import:

    ..  codeblock-pycon::

        >>> pt['__namespace__.ceil'] = 'math:ceil'
        >>> pt['y'] = '>>> int(ceil(3.1))'
        >>> pt['y']
        4

    """

    _method_sep = '#'
    _exp_prefix = '>>> '

    def __setitem__(self, key, value):
        if isinstance(value, string):
            if value.startswith(self._exp_prefix):
                if self._key_sep in key:
                    branch_key = key.rsplit(self._key_sep, 1)[0]
                    branch = self.branch(branch_key)
                else:
                    branch = self
                value = value[len(self._exp_prefix):]
                value = eval(
                    value,
                    {'self': self, 'branch': branch},
                    self.branch('__namespace__')
                )
            elif key.startswith('__namespace__' + self._key_sep):
                value = EntryPoint.parse('x={0}'.format(value)).load(False)
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

        enqueue([path])
        while queue:
            path = queue.popleft()
            self['__file__'] = path
            self['__dir__'] = os.path.dirname(path)
            ext = os.path.splitext(path)[1]
            with open(path) as f:
                data = self.loaders[ext](f)
                self.update(flatten(data))
            include = self.pop('__include__', [])
            if isinstance(include, string):
                include = [include]
            enqueue(include)
            del self['__file__'], self['__dir__']
