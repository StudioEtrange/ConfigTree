from sys import version_info
from collections import defaultdict, Mapping, MutableMapping
from pkg_resources import EntryPoint


__all__ = ['Tree', 'ProcessingTree', 'flatten']


if version_info[0] == 3:
    string = str
else:
    string = basestring     # NOQA


class Tree(MutableMapping):
    """
    A Tree is a dictionary like object, which supports nested keys.

    Examples:

    ..  code-block:: pycon

        >>> tree = Tree()
        >>> tree['a.b.c'] = 1
        >>> tree['a'] == {'b.c': 1}
        True
        >>> tree['a.b'] == {'c': 1}
        True
        >>> tree['a']['b'] == {'c': 1}
        True
        >>> tree['a.b']['d'] = 2
        >>> tree['a.b'] == {'c': 1, 'd': 2}
        True

    Tree object unable to create empty branch on demand:

    ..  code-block:: pycon

        >>> branch = tree['x.y']                        # DOCTEST: +ellipsis
        Traceback (most recent call last):
        ...
        KeyError: 'x.y'

    Use :meth:`branch` for this purposes.  It explicitly creates
    a :class:`BranchProxy` object tied to specified key:

    ..  code-block:: pycon

        >>> branch = tree.branch('x.y')
        >>> branch['z'] = 3
        >>> tree == {'a.b.c': 1, 'a.b.d': 2, 'x.y.z': 3}
        True

    An empty branch automatically collapses from Tree:

    ..  code-block:: pycon

        >>> del branch['z']
        >>> 'x.y' in tree
        False

    Tree object doesn't perform any implicit type inspection and conversion.
    It means what you put into tree is what you get from.  Even when you put
    one branch to another, Tree won't create a copy:

    ..  code-block:: pycon

        >>> tree['x'] = tree['a']
        >>> tree['x.b.c']                               # DOCTEST: +ellipsis
        Traceback (most recent call last):
        ...
        KeyError: 'x.b.c'
        >>> tree['x']['b.c']
        1
        >>> tree['x']['b.c'] = 3
        >>> tree['a.b.c']
        3

    It's a road to debug hell, don't follow it.

    """

    _key_sep = '.'

    def __init__(self, data=None):
        self._branches = defaultdict(set)
        self._items = {}
        if data:
            self.update(data)

    def __setitem__(self, key, value):
        if key in self._branches:
            del self[key]
        self._items[key] = value
        if self._key_sep in key:
            path = key.split(self._key_sep)
            for i in range(1, len(path)):
                lead = self._key_sep.join(path[:i])
                tail = self._key_sep.join(path[i:])
                if lead in self._items:
                    del self[lead]
                self._branches[lead].add(tail)

    def __getitem__(self, key):
        try:
            return self._items[key]
        except KeyError:
            if key not in self._branches:
                raise
            return self.branch(key)

    def __delitem__(self, key):
        try:
            del self._items[key]
            if self._key_sep in key:
                path = key.split(self._key_sep)
                for i in range(1, len(path)):
                    lead = self._key_sep.join(path[:i])
                    tail = self._key_sep.join(path[i:])
                    self._branches[lead].discard(tail)
                    if not self._branches[lead]:
                        del self._branches[lead]
        except KeyError:
            if key not in self._branches:
                raise
            self.branch(key).clear()

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self._items)

    def branch(self, key):
        """ Returns a :class:`BranchProxy` object for specified ``key`` """
        return BranchProxy(key, self)


class BranchProxy(MutableMapping):
    """
    A Branch Proxy is a helper object.  This kind of object
    is created on demand when you expose an intermediate key of
    :class:`Tree` object:

    ..  code-block:: pycon

        >>> tree = Tree({'a.b.c': 1})
        >>> branch = tree['a.b']
        >>> isinstance(branch, BranchProxy)
        True

    The class methods are similar to :class:`Tree` ones.
    Each method is just proxied to corresponding owner's one.

    """

    def __init__(self, key, owner):
        self._key = key
        self._owner = owner

    def _itemkey(self, key):
        return self._owner._key_sep.join((self._key, key))

    def keys(self):
        if self._key not in self._owner._branches:
            return set()
        return self._owner._branches[self._key]

    def __getitem__(self, key):
        return self._owner[self._itemkey(key)]

    def __setitem__(self, key, value):
        self._owner[self._itemkey(key)] = value

    def __delitem__(self, key):
        del self._owner[self._itemkey(key)]

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def branch(self, key):
        """ Returns a :class:`BranchProxy` object for specified ``key`` """
        return self._owner.branch(self._itemkey(key))

    def as_tree(self):
        """ Converts Branch into separate :class:`Tree` object """
        return self._owner.__class__(self)


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


def flatten(d, sep='.'):
    """
    A generator which flattens out passed nested mapping objects.

    It's useful in combination with :class:`Tree` constructor
    or :meth:`Tree.update`:

    ..  code-block:: pycon

        >>> fd = flatten({'a': {'b': {'c': 1}}})
        >>> Tree(fd)
        Tree({'a.b.c': 1})

    """
    for key, value in d.items():
        if isinstance(value, Mapping):
            for subkey, subvalue in flatten(value, sep=sep):
                yield ''.join((key, sep, subkey)), subvalue
        else:
            yield str(key), value
