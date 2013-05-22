import os
from pkg_resources import EntryPoint
from collections import deque

from .tree import Tree, flatten
from .compat import string
from .loader import load_json, load_yaml


class ProcessingTree(Tree):
    """
    A Processing Tree is sublcass of :class:`configtree.tree.Tree` which able
    to process items during update.

    First use case is list merging:

    ..  code-block:: pycon

        >>> pt = ProcessingTree({'a.b.c': [1, 2, 3]})
        >>> pt['a.b.c#extend'] = [4, 5, 6]
        >>> pt
        ProcessingTree({'a.b.c': [1, 2, 3, 4, 5, 6]})

    Next one is executing expression from string value:

    ..  code-block:: pycon

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

    Note, current branch and Tree object itself are passed into each expression
    under the names ``branch`` and ``self``.  You have to update
    :attr:`namespace` attribute to extend names available in expression:

    ..  code-block:: pycon

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
    A Configuration Tree is a subclass of :class:`ProcessingTree`, which
    is able to load its content from files.  See doc-string of :meth:`load`
    for details.

    It uses a class level attribute :attr:`loaders` to map source file to
    loader object.  Loaders for JSON and YAML are supported out of the box.
    See :mod:`configtree.loader` for details.

    """

    loaders = {
        '.json': load_json,
        '.yaml': load_yaml,
    }

    def load(self, *paths):
        """
        Load content of Tree from files.

        Accept path list as positional arguments.  Each path must be an
        absolute path to file or directory.  If path points directory, all
        files from the directory will be loaded, but not from subdirectories.
        Files from the directory will be processed in alphabetical order.

        File may contain a special keys ``__include__`` and ``__import__``.

        The key ``__include__`` must be a string or list of strings.  Each
        string represents an additional path to load.  These paths are
        processed in the same way as method arguments.  But these paths will
        be processed after method arguments.  If path is relative, it will be
        processed as relative to current directory.

        The key ``__import__`` must be a dictionary object.  It extends a
        attr:`namespace` attribute (see :class:`ProcessingTree`), but for
        current file only.  The dictionary must be in format
        ``{'alias': 'package.module:object_to_import'}``, i.e. values must
        contain an entry points (see :mod:`pkg_resources` module from standard
        library).

        The method extends :attr:`namespace` during file processing by special
        values ``__dir__`` and ``__file__``.  Each one contain an absolute
        path.

        Because of built-in loaders return :class:`OrderedDict` objects,
        key-value pairs are processed in the same order as written in the file.
        Feel free to use values in the expressions that follows them.

        """
        queue = deque()

        def abspath(relpath):
            if os.path.isabs(relpath):
                return relpath
            result = os.path.join(self.namespace['__dir__'], relpath)
            result = os.path.realpath(result)
            return result

        def enqueue(paths):
            for path in paths:
                path = abspath(path)
                if os.path.isfile(path) and \
                   os.path.splitext(path)[1] in self.loaders and \
                   path not in queue:
                    queue.append(path)
                elif os.path.isdir(path):
                    files = []
                    for name in os.listdir(path):
                        subpath = os.path.join(path, name)
                        if os.path.isfile(subpath):
                            files.append(subpath)
                    enqueue(sorted(files))

        global_namespace = self.namespace.copy()
        enqueue(paths)
        while queue:
            path = queue.popleft()
            self.namespace['__file__'] = path
            self.namespace['__dir__'] = os.path.dirname(path)
            ext = os.path.splitext(path)[1]
            with open(path) as f:
                data = self.loaders[ext](f)
                imports = data.pop('__import__', {})
                self.namespace.update((alias, _import(ep))
                                      for alias, ep in imports.items())
                self.update(flatten(data))
            include = self.pop('__include__', [])
            if isinstance(include, string):
                include = [include]
            enqueue(include)
            self.namespace = global_namespace


def _import(ep):
    if ep not in _import.cache:
        _import.cache[ep] = EntryPoint.parse('x={0}'.format(ep)).load(False)
    return _import.cache
_import.cache = {}
