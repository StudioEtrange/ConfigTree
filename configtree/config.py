import os
from pkg_resources import iter_entry_points, EntryPoint
from collections import deque

from .tree import Tree, flatten
from .compat import string


parsers = {}
for entry in iter_entry_points('configtree.parsers'):
    try:
        parsers[entry.name] = entry.load()
    except ImportError as e:
        pass


class ProcessingTree(Tree):
    """
    A Processing Tree is sublcass of :class:`Tree` which able to process
    items during update.

    First use case is list merging:

    ..  codeblock-pycon::

        >>> pt = ProcessingTree({'a.b.c': [1, 2, 3]})
        >>> pt.update({'a.b.c#extend': [4, 5, 6]})
        >>> pt
        ProcessingTree({'a.b.c': [1, 2, 3, 4, 5, 6]})

    Next one is executing expression from string value:

    ..  codeblock-pycon::

        >>> pt = ProcessingTree()
        >>> pt.update({'a.b.c': '>>> 1 + 1'})
        >>> pt['a.b.c']
        2
        >>> pt['a.b.d'] = ">>> self['a.b.c'] * 2"
        >>> pt['a.b.d']
        4
        >>> pt['a.b.e'] = ">>> branch['d'] + 2"
        >>> pt['a.b.e']
        6

    Update ``__locals__`` branch to extend expression namespace:

    ..  codeblock-pycon::

        >>> from datetime import date
        >>> pt['__locals__.date'] = date
        >>> pt['today'] = '>>> date.today()'
        >>> pt['today'] == date.today()
        True

    Any string passed to ``__locals__`` branch will be treated as name
    to import:

    ..  codeblock-pycon::

        >>> pt['__locals__.ceil'] = 'math:ceil'
        >>> pt['x'] = '>>> int(ceil(3.1))'
        >>> pt['x']
        4

    """

    _method_sep = '#'
    _exp_prefix = '>>> '

    def __setitem__(self, key, value):
        if isinstance(value, string):
            if value.startswith(self._exp_prefix):
                branch = None
                if self._key_sep in key:
                    branch_key = key.rsplit(self._key_sep, 1)[0]
                    branch = self.branch(branch_key)
                value = value[len(self._exp_prefix):]
                value = eval(value, {'self': self, 'branch': branch},
                                     self.branch('__locals__'))
            elif key.startswith('__locals__' + self._key_sep):
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
