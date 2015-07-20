""" The module provides utility functions to load tree object from files """

import os
import sys
import re

from cached_property import cached_property

from . import source
from .compat import string
from .tree import Tree, flatten


def worker(priority, enabled=True):

    def decorator(f):
        f.__worker__ = enabled
        f.__priority__ = priority
        return f

    return decorator


class Pipeline(object):

    @cached_property
    def __pipeline__(self):
        pipeline = []
        for worker in dir(self):
            if worker.startswith('_'):
                continue
            worker = getattr(self, worker)
            if not getattr(worker, '__worker__', False):
                continue
            pipeline.append(worker)
        pipeline.sort(key=lambda worker: worker.__priority__)
        return pipeline


class Walker(Pipeline):

    def __init__(self, **params):
        self.params = params

    def __call__(self, path):
        fileobj = File(
            os.path.dirname(path),
            os.path.basename(path),
            self.params,
        )
        for f in self.walk(fileobj):
            yield f.fullpath

    def walk(self, parent):
        if parent.isfile:
            yield parent
        elif parent.isdir:
            files = []
            for name in os.listdir(parent.fullpath):
                fileobj = File(parent.fullpath, name, parent.params)
                print(fileobj.fullpath)
                priority = None
                for modifier in self.__pipeline__:
                    priority = modifier(fileobj)
                    if priority is not None:
                        break
                if priority < 0:
                    continue
                files.append((priority, fileobj))
            for _, fileobj in sorted(files):
                for f in self.walk(fileobj):
                    yield f

    @worker(10)
    def ignored(self, fileobj):
        if fileobj.name.startswith('_') or fileobj.name.startswith('.'):
            return -1
        if fileobj.isfile and fileobj.ext not in source.map:
            return -1

    @worker(30)
    def final(self, fileobj):
        if not fileobj.name.startswith('final'):
            return None
        return 100 if fileobj.isdir else 101

    @worker(50)
    def environment(self, fileobj):
        if not fileobj.name.startswith('env-'):
            return None
        env = fileobj.cleanname.split('-', 1)[1]
        if not fileobj.params['env'].startswith(env):
            return -1
        fileobj.params['env'] = fileobj.params['env'][len(env) + 1:]
        return 51 if fileobj.isdir else 50

    @worker(1000)
    def regular(self, fileobj):
        return 31 if fileobj.isdir else 30


class File(object):

    def __init__(self, path, name, params):
        self.path = path
        self.name = name
        self.params = params.copy()

    def __lt__(self, other):
        return self.name < other.name

    @cached_property
    def fullpath(self):
        return os.path.join(self.path, self.name)

    @cached_property
    def isfile(self):
        return os.path.isfile(self.fullpath)

    @cached_property
    def isdir(self):
        return os.path.isdir(self.fullpath)

    @cached_property
    def ext(self):
        return os.path.splitext(self.name)[1]

    @cached_property
    def cleanname(self):
        return os.path.splitext(self.name)[0]


class Updater(Pipeline):

    def __init__(self, namespace=None):
        self.namespace = namespace or {}

    def __call__(self, tree, key, value, source):
        action = UpdateAction(tree, key, value, source)
        for modifier in self.__pipeline__:
            modifier(action)
        action()

    @worker(30)
    def set_default(self, action):
        if not action.key.endswith('?'):
            return
        action.key = action.key[:-1]

        def update(action):
            action.tree.setdefault(action.key, action.value)

        action.update = update

    @worker(30)
    def call_method(self, action):
        if '#' not in action.key:
            return
        action.key, method = action.key.split('#')

        def update(action):
            old_value = action.tree[action.key]
            if isinstance(old_value, Promise) or \
               isinstance(action.value, Promise):

                def deferred():
                    new_value = resolve(old_value)
                    getattr(new_value, method)(resolve(action.value))
                    return new_value

                action.tree[action.key] = action.promise(deferred)
            else:
                getattr(old_value, method)(action.value)

        action.update = update

    @worker(50)
    def format_value(self, action):
        if not isinstance(action.value, string) or \
           not action.value.startswith('$>> '):
            return
        value = action.value[4:]
        action.value = action.promise(
            lambda: value.format(
                self=ResolverProxy(action.tree),
                branch=ResolverProxy(action.branch),
            )
        )

    @worker(50)
    def printf_value(self, action):
        if not isinstance(action.value, string) or \
           not action.value.startswith('%>> '):
            return
        value = action.value[4:]
        action.value = action.promise(
            lambda: value % ResolverProxy(action.tree)
        )

    @worker(50)
    def eval_value(self, action):
        if not isinstance(action.value, string) or \
           not action.value.startswith('>>> '):
            return
        value = action.value[4:]
        action.value = action.promise(
            lambda: eval(
                value,
                self.namespace,
                {
                    'self': ResolverProxy(action.tree),
                    'branch': ResolverProxy(action.branch),
                }
            )
        )

    @worker(70)
    def required_value(self, action):
        if not isinstance(action.value, string) or \
           not action.value.startswith('!!!'):
            return
        action.value = Required(action.key, action.value[3:].strip())


class UpdateAction(object):

    def __init__(self, tree, key, value, source):
        self.tree = tree
        self.key = key
        self.value = value
        self.update = self.default_update

        # Debug info
        self._key = key
        self._value = value
        self._source = source

    @property
    def branch(self):
        if self.tree._key_sep not in self.key:
            return self.tree
        key = self.key.rsplit(self.tree._key_sep, 1)[0]
        return self.tree.branch(key)

    def promise(self, action):
        def wrapper():
            try:
                return action()
            except Exception as e:
                raise e.__class__(self, *e.args)
        return Promise(wrapper)

    def __repr__(self):
        return '<{key!r}: {value!r}> from {source}'.format(
            key=self._key,
            value=self._value,
            source=self._source,
        )

    @staticmethod
    def default_update(action):
        action.tree[action.key] = action.value

    def __call__(self):
        self.update(self)


class Promise(object):

    def __init__(self, action):
        self.action = action

    def __call__(self):
        return self.action()


def resolve(value):
    if isinstance(value, Promise):
        return value()
    return value


class ResolverProxy(object):

    def __init__(self, tree):
        self.__tree = tree

    def __getitem__(self, key):
        return resolve(self.__tree[key])

    def __getattr__(self, attr):
        return getattr(self.__tree, attr)


class Required(object):

    def __init__(self, key, comment):
        self.key = key
        self.comment = comment

    def __repr__(self):
        return 'Required(key={0.key!r}, comment={0.comment!r})'.format(self)


class PostProcessor(Pipeline):

    def __call__(self, tree):
        errors = []
        for key, value in tree.items():
            for modifier in self.__pipeline__:
                error = modifier(tree, key, value)
                if error is not None:
                    errors.append(error)
        if errors:
            errors.sort(key=lambda e: str(e))
            raise ProcessingError(errors)

    @worker(30)
    def resolve_promise(self, tree, key, value):
        if isinstance(value, Promise):
            tree[key] = value()

    @worker(50)
    def check_required(self, tree, key, value):
        if isinstance(value, Required):
            return value


class ProcessingError(Exception):
    pass


###############################################################################
# Deprecated features
##


def load(path, walk=None, update=None, postprocess=None, tree=None):
    """
    Loads :class:`configtree.tree.Tree` object from files.

    A ``path`` argument should be a path to the directory containing files
    to load.

    A ``walk`` argument, if provided should be a callable, which accepts
    ``path`` argument and returns an iterator over the files to load.
    By default, a function constructed by :func:`make_walk` is used.

    An ``update`` argument, if provided should be a callable, which accepts
    three arguments ``tree``, ``key``, ``value`` and performs update of
    ``tree`` using ``key`` and ``value`` pair.  By default, a function
    constructed by :func:`make_update` is used.

    A ``postprocess`` argument, if provided should be a callable, which accepts
    single argument ``tree``.  The loaded ``tree`` will be passed here.
    By default no post processing is done.  However, it's a good place
    to validate a result tree.

    A ``tree`` argument, if provided should be a tree-like object, which will
    be updated during the load process.  By default, an empty instance of
    :class:`configtree.tree.Tree` is used.  It is a right place to put
    some initial data or use derived class of :class:`configtree.tree.Tree`.

    """
    walk = walk or make_walk()
    update = update or make_update()
    tree = tree or Tree()
    for f in walk(path):
        ext = os.path.splitext(f)[1]
        with open(f) as data:
            tree['__file__'] = f
            tree['__dir__'] = os.path.dirname(f)
            for key, value in flatten(source.map[ext](data)):
                update(tree, key, value, f)
            del tree['__file__']
            del tree['__dir__']
    if postprocess is not None:
        postprocess(tree)
    return tree


def loaderconf(path):
    """
    Reads loader configuration from module ``loaderconf``.

    If file of the module does not exists, it will return an empty dictionary.
    Otherwise, the result will contain ``walk``, ``update``, ``postprocess``,
    and ``tree`` keys.

    Usage:

    ..  code-block:: python

        config = load(path, **loaderconf(path))

    """
    if path not in sys.path:
        sys.path.append(path)
    try:
        import loaderconf
        conf = loaderconf.__dict__
    except ImportError:
        conf = {}
    keys = ('walk', 'update', 'postprocess', 'tree')
    return dict((k, v) for k, v in conf.items() if k in keys)


def make_walk(env=''):
    """
    Constructs ``walk`` function, which will be used by :func:`load` one.

    The ``walk`` function recursively iterates over the directory and yields
    files to load.  It will skip:

        *   file, if its extension is not contained in the map of
            :mod:`configtree.source`.
        *   file or directory, if its name starts with "_" underscore or
            "." dot char (hidden one);
        *   file or directory, if its name starts with "env-" and the rest
            part of the name does not match environment name specified by
            the ``env`` argument.

    The files are emitted in the following order:

        1.  Top level common files.
        2.  Common files contained in the nested directories.
        3.  Environment specific files.
        4.  Files contained in the environment specific directories.
        5.  Files contained in the directories prefixed by "final-".
        6.  Top level files prefixed by "final-".

    All files are also sorted using natural sort within their groups.

    The environment is specified by ``env`` argument.  It supports tree-like
    environment configuration.  For instance, you have the following
    environments: ``dev`` (developer's one), ``test.staging``
    (for staging server), ``test.stress`` (for stress testing),
    and ``prod`` (for production usage).  The configuration files may be
    organized in the following way::

        config/
            common/
                common-config.yaml
            env-dev
                dev-config.yaml
            env-prod
                prod-config.yaml
            env-test
                common-test-config.yaml
                env-stress/
                    stress-test-config.yaml
                env-staging/
                    staging-server-config.yaml
            final-common/
                common-config.yaml

    So that, specifying ``env`` argument as ``test.staging``, will emit the
    following files in the exact order::

        config/common/common-config.yaml
        config/env-test/common-test-config.yaml
        config/env-test/env-staging/staging-server-config.yaml
        config/final-common/common-config.yaml

    """

    def walk(path, env=env):
        if '.' in env:
            env_name, tail = env.split('.', 1)
        else:
            env_name, tail = env, ''
        env_name = 'env-' + env_name
        files = []
        dirs = []
        env_files = []
        env_dirs = []
        final_files = []
        final_dirs = []
        for name in os.listdir(path):
            if name.startswith('_') or name.startswith('.'):
                continue
            fullname = os.path.join(path, name)
            if os.path.isdir(fullname):
                if name.startswith('env-'):
                    if name != env_name:
                        continue
                    target = env_dirs
                elif name.startswith('final-'):
                    target = final_dirs
                else:
                    target = dirs
                target.append(fullname)
            elif os.path.isfile(fullname):
                basename, ext = os.path.splitext(name)
                if ext not in source.map:
                    continue
                if basename.startswith('env-'):
                    if basename != env_name:
                        continue
                    target = env_files
                elif name.startswith('final-'):
                    target = final_files
                else:
                    target = files
                target.append(fullname)
        for f in sorted(files):
            yield f
        for d in sorted(dirs):
            for f in walk(d, env):
                yield f
        for f in sorted(env_files):
            yield f
        for d in sorted(env_dirs):
            for f in walk(d, tail):
                yield f
        for d in sorted(final_dirs):
            for f in walk(d, env):
                yield f
        for f in sorted(final_files):
            yield f

    return walk


def make_update(namespace=None):
    """
    Constructs ``update`` function, which will be used by :func:`load` one.

    The ``update`` function adds a pinch of syntactic sugar to loading
    :class:`configtree.tree.Tree` object from files:

    ..  code-block:: yaml

        x:
            a: 1
            b: 2
        y:
            b: 3

            # If a string value starts with ">>> ", it will be evaluated
            # as a Python expression. Where ``branch`` name refers to
            # the current tree branch, ``tree`` name refers to the whole
            # tree object.  Additionally, names passed via ``namespace``
            # argument can be used within the expression.
            c: ">>> tree['x.a'] + branch['b']"               # c == 4

            # If a string value starts with "$>> ", it will be used as
            # a template string.  It will be formatted used standard ``format``
            # method.  Only ``branch`` and ``tree`` names are available
            # within formatting.
            d: "$>> {tree[x.a]} + {branch[b]} = {branch[c]}" # d == "1 + 3 = 4"

            # If a key ends with "?", the corresponding value will be set
            # only if the key does not exists in the tree.  It is useful
            # to set default values, which could be already set within
            # another file.
            e: [1, 2]
            e?: []                                           # e == [1, 2]
            f?: []                                           # f == []

            # If a key contains "#", the part after that char will be used
            # as a method name.  This method will be called using the value.
            e#append: 3                                      # e == [1, 2, 3]

    """
    namespace = namespace or {}

    def update(tree, key, value, source=None):
        if key.endswith('?'):
            key = key[:-1]
            if key in tree:
                return
        if '#' in key:
            key, method = key.split('#')

            def set_value(k, v):
                getattr(tree[k], method)(v)
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
                    value = eval(value, namespace, local)
                else:
                    value = value.format(**local)
        set_value(key, value)

    return update
