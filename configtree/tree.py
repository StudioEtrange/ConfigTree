from abc import abstractmethod
from collections import defaultdict, Mapping, MutableMapping
from warnings import warn


__all__ = ['ITree', 'Tree', 'flatten', 'rarefy']


class ITree(MutableMapping):
    """
    Abstract base class for :class:`Tree` and :class:`BranchProxy`.

    Useful for type checking:

    ..  code-block:: pycon

        >>> tree = Tree({'x.y': 1})
        >>> tree
        Tree({'x.y': 1})
        >>> isinstance(tree, ITree)
        True
        >>> tree['x']
        BranchProxy('x'): {'y': 1}
        >>> isinstance(tree, ITree)
        True

    """

    _key_sep = '.'

    def rare_keys(self):
        """
        Returns an iterator over the first level keys.

        ..  code-block:: pycon

            >>> tree = Tree({'a.b.c': 1, 'k': 2, 'x.y.z': 3})
            >>> sorted(list(tree.rare_keys())) == ['a', 'k', 'x']
            True

        """
        branches = set()
        for key in self.keys():
            if self._key_sep not in key:
                yield key
                continue
            key = key.split(self._key_sep, 1)[0]
            if key not in branches:
                yield key
                branches.add(key)

    def rare_values(self):
        """
        Returns an iterator over the first level values.

        See :meth:`rare_keys`.

        """
        for key in self.rare_keys():
            yield self[key]

    def rare_items(self):
        """
        Returns an iterator over the first level items.

        See :meth:`rare_keys`

        """
        for key in self.rare_keys():
            yield key, self[key]

    @abstractmethod
    def copy(self):
        pass  # pragma: nocover

    def rare_copy(self):
        """
        Returns a rarefied copy of the tree.

        ..  code-block:: pycon

            >>> tree = Tree({'x.y.z': 1})
            >>> tree.rare_copy()
            {'x': {'y': {'z': 1}}}

        """
        return rarefy(self)

    @abstractmethod
    def branch(self, key):
        pass  # pragma: nocover


_void = object()


class Tree(ITree):
    """
    Tree is a dictionary like object, which supports nested keys.

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

    The tree object is unable to create an empty branch on demand:

    ..  code-block:: pycon

        >>> branch = tree['x.y']                        # DOCTEST: +ellipsis
        Traceback (most recent call last):
        ...
        KeyError: 'x.y'

    Use :meth:`branch` for this purposes.  It explicitly creates
    a :class:`BranchProxy` object tied to the specified key:

    ..  code-block:: pycon

        >>> branch = tree.branch('x.y')
        >>> branch['z'] = 3
        >>> tree == {'a.b.c': 1, 'a.b.d': 2, 'x.y.z': 3}
        True

    An empty branch automatically collapses from the Tree:

    ..  code-block:: pycon

        >>> del branch['z']
        >>> 'x.y' in tree
        False

    The tree object doesn't perform any implicit type inspection and
    conversion.  It means what you put into the tree is what you will get
    from one later.  Even when you put one branch to another, the Tree won't
    create a copy:

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

    It's a road to debug hell, don't follow it.  If you want to copy a branch,
    use :meth:`update` method.

    ..  code-block:: pycon

        >>> tree = Tree({'a.b.c': 1})
        >>> tree.branch('x').update(tree['a'])
        >>> tree == {'a.b.c': 1, 'x.b.c': 1}
        True
        >>> tree['x.b.c'] = 3
        >>> tree == {'a.b.c': 1, 'x.b.c': 3}
        True

    """

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

    def copy(self):
        """
        Returns a shallow copy of the tree.  The result has the same type.

        """
        return self.__class__(self)

    def pop(self, key, default=_void):
        """
        Removes specified key and returns the corresponding value.
        If key is not found, ``default`` is returned if given,
        otherwise KeyError is raised.

        If extracted value is a branch, it will be converted to :class:`Tree`.

        """
        try:
            value = self[key]
        except KeyError:
            if default is _void:
                raise
            return default
        else:
            if isinstance(value, BranchProxy):
                value = value.copy()
            del self[key]
            return value


class BranchProxy(ITree):
    """
    Branch Proxy is a helper object.  This kind of object
    is created on demand when you expose an intermediate key of
    the :class:`Tree` object:

    ..  code-block:: pycon

        >>> tree = Tree({'a.b.c': 1})
        >>> branch = tree['a.b']
        >>> isinstance(branch, BranchProxy)
        True

    The class methods are similar to :class:`Tree` ones.
    Each method is just proxied to corresponding owner's one.

    """

    def __init__(self, key, owner):
        self._key_sep = owner._key_sep
        self._key = key
        self._owner = owner

    def _itemkey(self, key):
        return self._key_sep.join((self._key, key))

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

    def __repr__(self):
        return '{0}({1!r}): {2!r}'.format(
            self.__class__.__name__,
            self._key,
            dict(self),
        )

    def branch(self, key):
        """ Returns a :class:`BranchProxy` object for specified ``key`` """
        return self._owner.branch(self._itemkey(key))

    def as_tree(self):
        """
        ..  warning:: Deprectated in favor of :meth:`copy`

        """
        warn(
            'Method ``as_tree`` is deprected in favor of ``copy`` one',
            DeprecationWarning,
        )
        return self.copy()

    def copy(self):
        """
        Returns a shallow copy of the branch.  The result has the same type
        as the branch owner, i.e. :class:`Tree` or derrived from one.

        """
        return self._owner.__class__(self)

    def pop(self, key, default=_void):
        """
        Removes specified key and returns the corresponding value.
        If key is not found, ``default`` is returned if given,
        otherwise KeyError is raised.

        If extracted value is a branch, it will be converted to :class:`Tree`.

        """
        return self._owner.pop(self._itemkey(key), default)


def flatten(d):
    """
    Generator which flattens out passed nested mapping objects.

    It's useful in combination with :class:`Tree` constructor
    or :meth:`Tree.update`:

    ..  code-block:: pycon

        >>> nested = {'a': {'b': {'c': 1}}}
        >>> Tree(nested)                        # without flatten
        Tree({'a': {'b': {'c': 1}}})
        >>> Tree(flatten(nested))               # with flatten
        Tree({'a.b.c': 1})

    """
    for key, value in d.items():
        if isinstance(value, Mapping):
            for subkey, subvalue in flatten(value):
                yield '{0}.{1}'.format(key, subkey), subvalue
        else:
            yield str(key), value


def rarefy(tree):
    """
    Converts passed flatten mapping object into a nested dictionary.

    It works oppositely to :func:`flatten`.

    ..  code-block:: pycon

        >>> rarefy(Tree({'a.b.c' : 1}))
        {'a': {'b': {'c': 1}}}
        >>> rarefy({'a.b.c' : 1})
        {'a': {'b': {'c': 1}}}

    """
    result = {}
    for key, value in tree.items():
        target = result
        if '.' in key:
            keyparts = key.split('.')
            key = keyparts.pop()
            for keypart in keyparts:
                target = target.setdefault(keypart, {})
        if isinstance(value, Mapping):
            value = rarefy(value)
        target[key] = value

    return result
