import os
import re
import pkg_resources

from . import source
from .compat import string
from .tree import Tree, flatten


class Loader(object):
    """
    A Loader is a callable object which loads :class:`configtree.tree.Tree`
    object from files.  It accepts three arguments during construction:
    ``walk``, ``update``, and ``factory``.

    The ``walk`` argument should be a callable object, which accepts single
    argument---path to configuration tree files.  It should return an iterator
    over the files to load and may filter out some files.
    By default :class:`Walker` is used.

    The ``update`` argument should be a callable object, which accepts three
    arguments: result configuration tree object, key, and value.
    It should set specified value under the specified key into result tree.
    So it may provide some syntactic sugar. By default :class:`Updater`
    is used.

    The ``factory`` argument should be a callable object, which constructs a
    result configuration tree object. By default class
    :class:`configtree.tree.Tree` is used.  This argument may be used, if you
    want to use your own class, for example derived from default one.

    """

    defaults = {
        'walk.factory': 'configtree.loader:Walker',
        'update.factory': 'configtree.loader:Updater',
        'factory': 'configtree.tree:Tree',
    }

    @classmethod
    def from_settings(cls, settings, path=None):

        def get_worker(settings):
            if isinstance(settings, string):
                return import_spec(settings)
            factory = import_spec(settings.pop('factory'))
            return factory(**settings)

        settings_ = Tree(cls.defaults)

        if path is not None:
            filename = os.path.join(path, '.settings')
            if os.path.isfile(filename):
                with open(filename) as data:
                    data = source.load_yaml(data)
                    if data:
                        settings_.update(data)

        settings_.update(settings)

        walk = get_worker(settings_['walk'])
        update = get_worker(settings_['update'])
        factory = import_spec(settings_['factory'])
        return cls(walk, update, factory)

    def __init__(self, walk=None, update=None, factory=None):
        self.walk = walk or Walker()
        self.update = update or Updater()
        self.factory = factory or Tree

    def __call__(self, path):
        result = self.factory()
        for f in self.walk(path):
            ext = os.path.splitext(f)[1]
            with open(f) as data:
                result['__file__'] = f
                result['__dir__'] = os.path.dirname(f)
                for key, value in flatten(source.map[ext](data)):
                    self.update(result, key, value)
                del result['__file__']
                del result['__dir__']
        return result


class Walker(object):

    def __init__(self, env=''):
        self.env = env

    def __call__(self, path, env=None):
        if env is None:
            env = self.env
        if '.' in env:
            env_name, tail = env.split('.', 1)
        else:
            env_name, tail = env, ''
        env_name = 'env-' + env_name
        files = []
        dirs = []
        env_files = []
        env_dirs = []
        for name in os.listdir(path):
            if name.startswith('_'):
                continue
            fullname = os.path.join(path, name)
            if os.path.isdir(fullname):
                if name.startswith('env-'):
                    if name != env_name:
                        continue
                    target = env_dirs
                else:
                    target = dirs
                target = env_dirs if name.startswith('env-') else dirs
                target.append(fullname)
            elif os.path.isfile(fullname):
                basename, ext = os.path.splitext(name)
                if ext not in source.map:
                    continue
                if basename.startswith('env-'):
                    if basename != env_name:
                        continue
                    target = env_files
                else:
                    target = files
                target.append(fullname)
        for f in sorted(files):
            yield f
        for d in sorted(dirs):
            for f in self(d, env):
                yield f
        for f in sorted(env_files):
            yield f
        for d in sorted(env_dirs):
            for f in self(d, tail):
                yield f


class Updater(object):

    def __init__(self, namespace=None):
        self.namespace = namespace or {}
        for key, value in self.namespace.items():
            if isinstance(value, string):
                self.namespace[key] = import_spec(value)

    def __call__(self, tree, key, value):
        if key.endswith('?'):
            key = key[:-1]
            if key in tree:
                return
        if '#' in key:
            key, method = key.split('#')
            set_value = lambda k, v: getattr(tree[k], method)(v)
        else:
            set_value = tree.__setitem__
        if isinstance(value, string):
            match = re.match('(?:\$|>)>> ', value)
            if match:
                prefix = match.group(0)
                if tree._key_sep in key:
                    branch_key = key.rsplit(tree._key_sep, 1)[0]
                    branch = tree.branch(branch_key)
                else:
                    branch = tree
                value = value[4:]  # Remove prefix
                local = {'self': tree, 'branch': branch}
                if prefix == '>>> ':
                    value = eval(value, self.namespace, local)
                else:
                    value = value.format(**local)
        set_value(key, value)


def import_spec(spec):
    entry_point = 'x={0}'.format(spec)
    entry_point = pkg_resources.EntryPoint.parse(entry_point)
    return entry_point.load(False)
