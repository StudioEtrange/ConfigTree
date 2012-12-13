""" The module contains base :class:`Tree` and utility stuff """

from collections import defaultdict, Mapping, MutableMapping


__all__ = ['Tree', 'flatten']


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

    An empty brach automatically collapses from Tree:

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

    def __init__(self, data=None, sep='.'):
        self._sep = sep
        self._branches = defaultdict(set)
        self._items = {}
        if data:
            self.update(data)

    def __setitem__(self, key, value):
        if key in self._branches:
            del self[key]
        self._items[key] = value
        if self._sep in key:
            path = key.split(self._sep)
            for i in range(1, len(path)):
                lead = self._sep.join(path[:i])
                tail = self._sep.join(path[i:])
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
            if self._sep in key:
                path = key.split(self._sep)
                for i in range(1, len(path)):
                    lead = self._sep.join(path[:i])
                    tail = self._sep.join(path[i:])
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
        return '{0}({1!r}, sep={2!r})'.format(self.__class__.__name__,
                                              self._items, self._sep)

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
        return self._owner._sep.join((self._key, key))

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
        return self._owner.__class__(self, sep=self._owner._sep)


def flatten(d, sep='.'):
    """
    A generator which flattens out passed nested mapping objects.

    It's useful in combination with :class:`Tree` constructor
    or :meth:`Tree.update`:

    ..  code-block:: pycon

        >>> fd = flatten({'a': {'b': {'c': 1}}})
        >>> Tree(fd)
        Tree({'a.b.c': 1}, sep='.')

    """
    for key, value in d.items():
        if isinstance(value, Mapping):
            for subkey, subvalue in flatten(value, sep=sep):
                yield ''.join((key, sep, subkey)), subvalue
        else:
            yield str(key), value
