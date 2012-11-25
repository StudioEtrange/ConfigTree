from collections import defaultdict, Mapping, MutableMapping


class Tree(MutableMapping):

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
        return BranchProxy(key, self)


class BranchProxy(MutableMapping):

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
        return self._owner.branch(self._itemkey(key))

    def as_tree(self):
        return self._owner.__class__(self, sep=self._owner._sep)


def flatten(d, sep='.'):
    for key, value in d.items():
        if isinstance(value, Mapping):
            for subkey, subvalue in flatten(value, sep=sep):
                yield '{0}{1}{2}'.format(key, sep, subkey), subvalue
        else:
            yield str(key), value
