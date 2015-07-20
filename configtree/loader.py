""" The module provides utility functions to load tree object from files """

import os
import sys
import re

from cached_property import cached_property

from . import source
from .compat import string
from .tree import Tree, flatten


class Loader(object):

    def __init__(self, walk=None, update=None, postprocess=None, tree=None):
        self.walk = walk or Walker()
        self.update = update or Updater()
        self.postprocess = postprocess or PostProcessor()
        self.tree = tree or Tree()

    @classmethod
    def fromconf(cls, path):
        """ Creates loader using configuration module ``loaderconf`` """
        if path not in sys.path:
            sys.path.append(path)
        try:
            import loaderconf
            conf = loaderconf.__dict__
        except ImportError:
            conf = {}
        keys = ('walk', 'update', 'postprocess', 'tree')
        conf = dict((k, v) for k, v in conf.items() if k in keys)
        return cls(**conf)

    def __call__(self, path):
        for f in self.walk(path):
            ext = os.path.splitext(f)[1]
            with open(f) as data:
                data = source.map[ext](data)
                if not data:
                    continue
                for key, value in flatten(data):
                    self.update(self.tree, key, value, f)
        if self.postprocess is not None:
            self.postprocess(self.tree)
        return self.tree


###############################################################################
# Utilities
##


def worker(priority, enabled=True):
    """
    Decorator that marks :class:`Pipeline` method as a worker

    :param int priority: Priority of the worker
    :param bool enabled: Whether worker is active or not

    """

    def decorator(f):
        f.__worker__ = enabled
        f.__priority__ = priority
        return f

    return decorator


class Pipeline(object):
    """
    Utility class that helps to build pipelines

    ..  attribute:: __pipeline__

        List of workers that includes each method of the class that marked
        by :func:`worker` decorator.  The list is sorted by worker priority.
        Inactive workers are not included in the list.

    """

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


###############################################################################
# Walker
##


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
        if not fileobj.params.get('env', '').startswith(env):
            return -1
        fileobj.params['env'] = fileobj.params['env'][len(env) + 1:]
        return 51 if fileobj.isdir else 50

    @worker(1000)
    def regular(self, fileobj):
        return 31 if fileobj.isdir else 30


class File(object):
    """
    Represents current traversing file within :class:`Walker` routine

    ..  attribute:: path

        Path of parent directory containing the file

    ..  attribute:: name

        File name itself

    ..  attribute:: fullpath

        Full path to the file

    ..  attribute:: isdir

        Whether the file is directory

    ..  attribute:: isfile

        Whether the file is regular file

    ..  attribute:: ext

        Extension of the file (with leading dot char)

    ..  attribute:: cleanname

        Name of the file without its extension

    """

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


###############################################################################
# Updater
##


class Updater(Pipeline):
    """
    Updater factory

    :param dict namespace: See :attr:`namespace`.

    ..  attribute:: namespace

        A dictionary that is passed into evaluated expressions as ``globals``
        parameter.  The namespace may contain some non-built-in functions,
        that could be used within expression.

    ..  attribute:: __pipeline__

        [:meth:`set_default`, :meth:`call_method`, :meth:`format_value`,
        :meth:`printf_value`, :meth:`eval_value`, :meth:`required_value`]

    """

    def __init__(self, namespace=None):
        self.namespace = namespace or {}

    def __call__(self, tree, key, value, source):
        """
        Updates tree

        It creates :class:`UpdateAction` object.  Then pass the object through
        :attr:`__pipeline__`.  And finally calls the action object.

        :param Tree tree: Updating tree object
        :param str key: Setting up key
        :param value: Setting up value
        :param str source: Full path to a source file

        """
        action = UpdateAction(tree, key, value, source)
        for modifier in self.__pipeline__:
            modifier(action)
        action()

    @worker(30)
    def set_default(self, action):
        """
        Worker that changes default update action if key ends with "?" char.

        It strips the last char of the key.  It will set passed value,
        if the result key is not exist in updating tree.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 30

        Example:

            ..  code-block:: yaml

                x: 1
                x?: 2           # x == 1
                y?: 3           # y == 3


        """
        if not action.key.endswith('?'):
            return
        action.key = action.key[:-1]

        def update(action):
            action.tree.setdefault(action.key, action.value)

        action.update = update

    @worker(30)
    def call_method(self, action):
        """
        Worker that changes default update action if key contains "#" char.

        It splits key by the char.  The left part is used as key itself.
        The right part is used as a method name.  It gets a value from
        updating tree by the new key and call the method using passed value
        as an argument.  If the value contains :class:`Promise`, it will
        wrap the action by another :class:`Promise` object.
        See :meth:`PostProcessor.resolve_promise`.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 30

        Example:

            ..  code-block:: yaml

                foo: [1, 2]
                bar: ">>> self['foo'][:]"        # Get copy of the latest `foo`
                bar#extend: [5, 6]               # bar == [1, 2, 3, 4, 5, 6]
                foo#extend: [3, 4]               # foo == [1, 2, 3, 4]

        """
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
        """
        Worker that transform string value that starts with ``"$>> "``
        (with trailing space char) into formatting expression and wraps it
        into :class:`Promise`.  See :meth:`PostProcessor.resolve_promise`.

        The expression uses :meth:`str.format`.  Current tree and current
        branch are passed as ``self`` and ``branch`` names into template.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 50

        Example:

            ..  code-block:: yaml

                a: "foo"
                b:
                    x: "bar"
                    y: "a = {self[a]!r}, b.x = {branch[x]!r}"
                       # == "a = 'foo', b.x = 'bar'"

        """
        if not isinstance(action.value, string) or \
           not action.value.startswith('$>> '):
            return
        value = action.value[4:]
        action.value = action.promise(
            lambda: value.format(
                self=ResolverProxy(action.tree, action.source),
                branch=ResolverProxy(action.branch),
            )
        )

    @worker(50)
    def printf_value(self, action):
        """
        Worker that transform string value that starts with ``"%>> "``
        (with trailing space char) into formatting expression and wraps it
        into :class:`Promise`.  See :meth:`PostProcessor.resolve_promise`.

        The expression uses printf style, i.e. ``%`` operator.  Current tree
        is used as formatting value.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 50

        Example:

            ..  code-block:: yaml

                name: "World"
                hello: "%>> Hello %(name)s"     # == "Hello World"

        """
        if not isinstance(action.value, string) or \
           not action.value.startswith('%>> '):
            return
        value = action.value[4:]
        action.value = action.promise(
            lambda: value % ResolverProxy(action.tree, action.source)
        )

    @worker(50)
    def eval_value(self, action):
        """
        Worker that transform string value that starts with ``">>> "``
        (with trailing space char) into expression and wraps it
        into :class:`Promise`.  See :meth:`PostProcessor.resolve_promise`.

        The expression uses built-in function :func:`eval`.
        :attr:`namespace` is passed as ``gloabls`` argument of ``eval``.
        Current tree is passed as ``self`` and current branch is passed as
        ``branch`` names via ``locals`` argument of ``eval``.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 50

        Example:

            ..  code-block:: yaml

                a: ">>> 1 + 2"                         # == 3
                b:
                    x: 3
                    y: ">>> self['a'] * branch['x']"   # == 9

        """
        if not isinstance(action.value, string) or \
           not action.value.startswith('>>> '):
            return
        value = action.value[4:]
        action.value = action.promise(
            lambda: eval(
                value,
                self.namespace,
                {
                    'self': ResolverProxy(action.tree, action.source),
                    'branch': ResolverProxy(action.branch),
                }
            )
        )

    @worker(70)
    def required_value(self, action):
        """
        Worker that transform string value that starts with ``"!!!"`` into
        an instance of :class:`Required`.
        See :meth:`PostProcessor.check_required`.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 70

        Example:

            ..  code-block:: yaml

                foo: "!!!"                              # without comment
                bar: "!!! This should be redefined"     # with comment

        """
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
        self.source = source

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
            source=self.source,
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

    def __init__(self, tree, source=None):
        self.__tree = tree
        self.__source = source

    def __getitem__(self, key):
        try:
            return resolve(self.__tree[key])
        except KeyError:
            if self.__source is not None:
                if key == '__file__':
                    return self.__source
                elif key == '__dir__':
                    return os.path.dirname(self.__source)
            raise

    def __getattr__(self, attr):
        return getattr(self.__tree, attr)


class Required(object):

    def __init__(self, key, comment):
        self.key = key
        self.comment = comment

    def __repr__(self):
        return 'Required(key={0.key!r}, comment={0.comment!r})'.format(self)


###############################################################################
# Post Processor
##


class PostProcessor(Pipeline):
    """
    Post processor factory

    Post processor iterates over passed :class:`Tree` object and pass its
    keys and values through :attr:`__pipeline__`.  If any worker of
    the pipeline returns non ``None`` value, this value will be treated
    as an error.  Such errors are accumulated and raised within
    :class:`ProcessingError` exception at the end of processing.

    ..  attribute:: __pipeline__

        [:meth:`resolve_promise`, :meth:`check_required`]

    """

    def __call__(self, tree):
        """
        Runs post processor

        :param Tree tree: A tree object to process

        """
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
        """
        Worker that resolves :class:`Promise` objects.

        Any exception raised within promise expression will not be caught.

        :param Tree tree: Current processing tree
        :param str key: Current traversing key
        :param value: Current traversing value

        ..  attribute:: __priority__ = 30

        """
        if isinstance(value, Promise):
            tree[key] = value()

    @worker(50)
    def check_required(self, tree, key, value):
        """
        Worker that checks tree for raw :class:`Required` values.

        :param Tree tree: Current processing tree
        :param str key: Current traversing key
        :param value: Current traversing value
        :returns: ``None`` if value is not instance of :class:`Required`,
                  or value itself (that will be treated as an error)

        ..  attribute:: __priority__ = 50

        """
        if isinstance(value, Required):
            return value


class ProcessingError(Exception):
    """ Exception that will be raised, if post processor gets any error """


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
            data = source.map[ext](data)
            if not data:
                continue
            tree['__file__'] = f
            tree['__dir__'] = os.path.dirname(f)
            for key, value in flatten(data):
                update(tree, key, value)
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

    def update(tree, key, value):
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
