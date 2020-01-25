""" The module provides utility functions to load tree object from files """

import os
import sys

from cached_property import cached_property

from . import source
from .compat.types import basestr
from .tree import Tree, flatten


class Loader(object):
    """
    Configuration tree loader

    :param Walker walk: Walk actor that generates list of files to load
    :param Updater update: Update actor that implements syntactic sugar
    :param PostProcessor postprocess: Result tree post processor
    :param Tree tree: Tree object that should contain result of loading

    """

    def __init__(self, walk=None, update=None, postprocess=None, tree=None):
        self.walk = walk or Walker()
        self.update = update or Updater()
        self.postprocess = postprocess or PostProcessor()
        self.tree = tree if tree is not None else Tree()

    @classmethod
    def fromconf(cls, path):
        """
        Creates loader using configuration module ``loaderconf``

        :param str path: Path to a directory that contains ``loaderconf``
        :returns: Ready to use loader object
        :rtype: Loader

        """
        if path not in sys.path:
            sys.path.append(path)
        try:
            import loaderconf

            conf = loaderconf.__dict__
        except ImportError as e:
            # Get module name from exception meessage:
            #   Python 2.x "No module named module_name"
            #   Python 3.x "No module named 'module_name'"
            module_name = str(e).split()[-1].strip("'")
            if module_name != "loaderconf":
                raise
            conf = {}
        keys = ("walk", "update", "postprocess", "tree")
        conf = dict((k, v) for k, v in conf.items() if k in keys)
        return cls(**conf)

    def __call__(self, path):
        """
        Loads configuration

        :param str path: Path to a directory that contains configuration files.
        :returns: Result tree object
        :rtype: Tree

        """
        from . import logger

        logger.info('Walking over "%s"', path)
        for f in self.walk(path):
            relpath = os.path.relpath(f, path)
            logger.info('Loading "%s"', relpath)
            ext = os.path.splitext(f)[1]
            with open(f) as data:
                data = source.map[ext](data)
                if not data:
                    continue
                for key, value in flatten(data):
                    self.update(self.tree, key, value, f)
        logger.info("Post-processing")
        self.postprocess(self.tree)
        return self.tree


###############################################################################
# Utilities
##


class Pipeline(object):
    """
    Utility class that helps to build pipelines

    ..  attribute:: __pipeline__

        List of workers that includes each method of the class that marked
        by :meth:`worker` decorator.  The list is sorted by worker priority.
        Inactive workers are not included in the list.

    """

    @cached_property
    def __pipeline__(self):
        pipeline = []
        for worker in dir(self):
            if worker.startswith("_"):
                continue
            worker = getattr(self, worker)
            if not getattr(worker, "__worker__", False):
                continue
            pipeline.append(worker)
        pipeline.sort(key=lambda worker: worker.__priority__)
        return pipeline

    @staticmethod
    def worker(priority, enabled=True):
        """
        Decorator that marks method as a worker

        :param int priority: Priority of the worker
        :param bool enabled: Whether worker is active or not

        """

        def decorator(f):
            f.__worker__ = enabled
            f.__priority__ = priority
            return f

        return decorator


###############################################################################
# Walker
##


class Walker(Pipeline):
    """
    File walker is used by :class:`Loader` to get list of files to load.

    ..  attribute:: params

        Dictionary that contains all keyword arguments that are passed
        into constructor.  The dictionary is copied into each :class:`File`
        object into :attr:`File.params` attribute.  This attribute
        can be used by workers from :attr:`__pipeline__` to make decisions
        about the file priority.

        Only the ``env`` parameter makes sense for :meth:`environment` worker.
        All other parameters are simply ignored, but could be used
        in extensions.

    ..  attribute:: __pipeline__

        File processing pipeline.  Each :class:`File` object is passed
        through the following methods until some method returns ``int`` value.
        The special value ``-1`` means that the passed file should be ignored.
        Other values mean file priority.  For instance, regular files
        (see :meth:`regular`) have priorities equal to ``30`` or ``31``, and
        final ones (see :meth:`final`) have ``100`` or ``101``.  That means
        that final files will be at the end of result list of files, and
        regular files will be at the start of the list.

        The list of workers is:
        [:meth:`ignored`, :meth:`final`, :meth:`environment`, :meth:`regular`]

    """

    def __init__(self, **params):
        self.params = params

    def __call__(self, path):
        """
        Walks over the ``path`` and yields files to load

        :param str path: Path to walk over

        """
        fileobj = File(os.path.dirname(path), os.path.basename(path), self.params)
        for f in self.walk(fileobj):
            yield f.fullpath

    def walk(self, current):
        """
        Processes current traversing file

        If ``current`` is regular file, it will be yielded as is.
        If it is directory, the list of its files will be prioritized
        using :attr:`__pipeline__`.  Then the list will be sorted using
        given priorities and each file will be processed using this method
        recursively.

        The method is low level implementation of :meth:`__call__`
        and should not be used directly.

        :param File current: Current traversing file

        """
        if current.isfile:
            yield current
        elif current.isdir:
            files = []
            for name in os.listdir(current.fullpath):
                fileobj = File(current.fullpath, name, current.params)
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

    @Pipeline.worker(10)
    def ignored(self, fileobj):
        """
        Worker that filters out ignored files and directories

        The file will be ignored, if its name starts with dot char
        or underscore, or the file format is not supported by loader.

        :param File fileobj: Current traversing file
        :returns: * ``-1`` when the file is ignored one;
                  * ``None`` when the file is not ignored one.

        ..  attribute:: __priority__ = 10

        Examples::

            .hidden             # returns -1 (file name starts with dot char)
            _ignored            # returns -1 (file name starts with underscore)
            unsupported.txt     # returns -1 (txt files are not supported)
            other.yaml          # returns None

        """
        if fileobj.name.startswith("_") or fileobj.name.startswith("."):
            return -1
        if fileobj.isfile and fileobj.ext not in source.map:
            return -1

    @Pipeline.worker(30)
    def final(self, fileobj):
        """
        Worker that checks whether current traversing file is final or not.

        Final files are processed at the end of current list of files.
        If the file name starts with "final", it will be treated as final one.

        :param File fileobj: Current traversing file
        :returns: * ``100`` when the file is final one and it is directory;
                  * ``101`` when the file is final one and it is regular file;
                  * ``None`` when the file is not final one.

        ..  attribute:: __priority__ = 30

        Examples::

            final/           # returns 100
            final-dir/       # returns 100
            other-dir/       # returns None
            final.yaml       # returns 101
            final-file.json  # returns 101
            other.yaml       # returns None

        """
        if not fileobj.name.startswith("final"):
            return None
        return 100 if fileobj.isdir else 101

    @Pipeline.worker(50)
    def environment(self, fileobj):
        """
        Worker that checks whether current traversing file is environment
        specific or not.

        The file will be treated as environment specific, if its name starts
        with "env-" string.  The rest part of the name (without extension)
        is treated as environment name.  If the environment name does not
        match to ``env`` parameter (see :attr:`params`), then the file
        will be ignored.

        :param File fileobj: Current traversing file
        :returns: * ``-1`` when the file is environment specific,
                    but environment name is not match;
                  * ``50`` when the file is environment specific
                    and it is regular file;
                  * ``51`` when the file is environment specific
                    and it is directory;
                  * ``None`` when the file is not environment specific one.

        ..  attribute:: __priority__ = 50

        Examples::

            # params['env'] == "foo.bar"

            env-foo.yaml      # returns 50
            env-bar.yaml      # returns -1 (environment name is not match)
            env-foo/          # returns 51
                env-bar.yaml  # returns 50
                env-baz.yaml  # returns -1
                other.yaml    # returns None

        """
        if not fileobj.name.startswith("env-"):
            return None
        env = fileobj.cleanname.split("-", 1)[1]
        effective_env = fileobj.params.get("env", "")
        if effective_env != env and not effective_env.startswith(env + "."):
            return -1
        fileobj.params["env"] = effective_env[len(env) + 1 :]  # noqa
        return 51 if fileobj.isdir else 50

    @Pipeline.worker(1000)
    def regular(self, fileobj):
        """
        Worker that treats any file as a regular one.  The worker should be
        the last in the :attr:`__pipeline__`, because it does not make
        any check.

        :param File fileobj: Current traversing file
        :returns: * ``30`` when the file is regular file;
                  * ``31`` when the file is directory.

        ..  attribute:: __priority__ = 1000

        """
        return 31 if fileobj.isdir else 30


class File(object):
    """
    Represents current traversing file within :class:`Walker` routine

    ..  attribute:: path

        Path of parent directory containing the file

    ..  attribute:: name

        File name itself

    ..  attribute:: params

        The copy of :attr:`Walker.params` that could be used and transformed
        by workers from :attr:`Walker.__pipeline__`.
        See :meth:`Walker.environment`.

    ..  attribute:: fullpath

        Full path to the file

    ..  attribute:: isdir

        Boolean value that means whether the file is directory or not

    ..  attribute:: isfile

        Boolean value that means whether the file is regular file or not

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
    Updater is used by :class:`Loader` to set up key-value pairs into
    updating tree object.  The object extends default updating mechanism
    adding some syntactic sugar.

    ..  attribute:: params

        Dictionary that contains all keyword arguments that are passed
        into constructor.  The attribute can be used by workers.

        Only the ``namespace`` parameter makes sense for :meth:`eval_value`
        worker.  All other parameters are simply ignored, but could be used
        in extensions.

    ..  attribute:: __pipeline__

        Transforms :class:`UpdateAction` object that created by
        :meth:`__call__`.

        Each :class:`UpdateAction` object is passed through the following
        methods.  Each method can transform :attr:`UpdateAction.key`,
        :attr:`UpdateAction.value`, or :attr:`UpdateAction.update`, attributes.
        So that the default behavior of :class:`UpdateAction` can be changed.

        The list of workers is:
        [:meth:`set_default`, :meth:`call_method`, :meth:`format_value`,
        :meth:`printf_value`, :meth:`eval_value`, :meth:`required_value`]

    """

    def __init__(self, **params):
        self.params = params

    def __call__(self, tree, key, value, source):
        """
        Updates tree

        It creates :class:`UpdateAction` object.  Then pass the object through
        the :attr:`__pipeline__`.  And finally calls the action.

        :param Tree tree: Updating tree object
        :param str key: Setting up key
        :param value: Setting up value
        :param str source: Full path to a source file

        """
        action = UpdateAction(tree, key, value, source)
        for modifier in self.__pipeline__:
            modifier(action)
        action()

    @Pipeline.worker(20)
    def set_default(self, action):
        """
        Worker that changes default :attr:`UpdateAction.update` from
        ``__setitem__`` to ``setdefault`` if key ends with "?" char.

        It also transforms key, i.e. strips the last char.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 20

        Example:

            ..  code-block:: yaml

                x: 1
                x?: 2           # x == 1
                y?: 3           # y == 3


        """
        if not action.key.endswith("?"):
            return
        action.key = action.key[:-1]

        def update(action):
            action.tree.setdefault(action.key, action.value)

        action.update = update

    @Pipeline.worker(30)
    def call_method(self, action):
        """
        Worker that changes default :attr:`UpdateAction.update` if key contains
        "#" char.

        It splits :attr:`UpdateAction.key` by the char.  The left part is set
        up as the key itself.  The right part is used as a method name.
        It gets value from :attr:`UpdateAction.tree` by the new key and call
        its method using :attr:`UpdateAction.value` as an argument.
        If any of the values is instance of :class:`Promise`, then it will be
        wrapped by another :class:`Promise` object.
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
        if "#" not in action.key:
            return
        action.key, method = action.key.split("#")

        def update(action):
            old_value = action.tree[action.key]
            if isinstance(old_value, Promise) or isinstance(action.value, Promise):

                def deferred():
                    new_value = Promise.resolve(old_value)
                    getattr(new_value, method)(Promise.resolve(action.value))
                    return new_value

                action.tree[action.key] = action.promise(deferred)
            else:
                getattr(old_value, method)(action.value)

        action.update = update

    @Pipeline.worker(50)
    def format_value(self, action):
        """
        Worker that transforms :attr:`UpdateAction.value` that starts
        with ``"$>> "`` (with trailing space char) into formatting expression
        and wraps it into :class:`Promise`.
        See :meth:`PostProcessor.resolve_promise`.

        The expression uses :meth:`str.format`.  Current tree and current
        branch are passed as ``self`` and ``branch`` names into template.
        Both are wrapped by :class:`ResolverProxy`.

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
        if not isinstance(action.value, basestr) or not action.value.startswith("$>> "):
            return
        value = action.value[4:]
        action.value = action.promise(
            lambda: value.format(
                self=ResolverProxy(action.tree, action.source),
                branch=ResolverProxy(action.branch),
            )
        )

    @Pipeline.worker(60)
    def printf_value(self, action):
        """
        Worker that transform :attr:`UpdateAction.value` that starts
        with ``"%>> "`` (with trailing space char) into formatting expression
        and wraps it into :class:`Promise`.
        See :meth:`PostProcessor.resolve_promise`.

        The expression uses printf style, i.e. ``%`` operator.
        :attr:`UpdateAction.tree` wrapped by :class:`ResolverProxy`
        is used as a formatting value.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 60

        Example:

            ..  code-block:: yaml

                name: "World"
                hello: "%>> Hello %(name)s"     # == "Hello World"

        """
        if not isinstance(action.value, basestr) or not action.value.startswith("%>> "):
            return
        value = action.value[4:]
        action.value = action.promise(
            lambda: value % ResolverProxy(action.tree, action.source)
        )

    @Pipeline.worker(70)
    def eval_value(self, action):
        """
        Worker that transform :attr:`UpdateAction.value` that starts with
        ``">>> "`` (with trailing space char) into expression and wraps it
        into :class:`Promise`.  See :meth:`PostProcessor.resolve_promise`.

        The expression uses built-in function :func:`eval`.
        The value of ``namespace`` key from :attr:`params` is passed as
        ``gloabls`` argument of ``eval``.  :attr:`UpdateAction.tree` is passed
        as ``self`` and `UpdateAction.branch` is passed as ``branch`` names
        via ``locals`` argument of ``eval``.  Both are wrapped
        by :class:`ResolverProxy`.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 70

        Example:

            ..  code-block:: pycon

                >>> from math import floor
                >>> update = Updater(namespace={'floor': floor})

            ..  code-block:: yaml

                a: ">>> 1 + 2"                         # == 3
                b:
                    x: 3
                    y: ">>> self['a'] * branch['x']"   # == 9
                    z: ">>> floor(3.0 / 2)"            # == 1

        """
        if not isinstance(action.value, basestr) or not action.value.startswith(">>> "):
            return
        value = action.value[4:]
        namespace = self.params.get("namespace", {})
        action.value = action.promise(
            lambda: eval(
                value,
                namespace,
                {
                    "self": ResolverProxy(action.tree, action.source),
                    "branch": ResolverProxy(action.branch),
                },
            )
        )

    @Pipeline.worker(80)
    def required_value(self, action):
        """
        Worker that transform :attr:`UpdateAction.value` that starts with
        ``"!!!"`` into an instance of :class:`Required`.
        See :meth:`PostProcessor.check_required`.

        :param UpdateAction action: Current update action object

        ..  attribute:: __priority__ = 80

        Example:

            ..  code-block:: yaml

                foo: "!!!"                              # without comment
                bar: "!!! This should be redefined"     # with comment

        """
        if not isinstance(action.value, basestr) or not action.value.startswith("!!!"):
            return
        action.value = Required(action.key, action.value[3:].strip())


class UpdateAction(object):
    """
    Helper object that is used within :class:`Updater` routine.
    It represents current update context.

    ..  attribute:: tree

        Current updating :class:`configtree.tree.Tree` object

    ..  attribute:: branch

        Property that is used to get current branch from the tree

        ..  code-block:: pycon

            >>> tree = Tree({'a.x': 1, 'a.y': 2})
            >>> action = UpdateAction(tree, 'a.z', 3, '/path/to/src.yaml')
            >>> action.branch == tree['a']
            True

    ..  attribute:: key

        Current setting up key

    ..  attribute:: value

        Current setting up value

    ..  attribute:: source

        Path to a file processing by :class:`Loader`.  Is used as a part
        of debug information.

        ..  code-block:: pycon

            >>> UpdateAction(Tree(), 'foo', 'bar', '/path/to/src.yaml')
            <tree['foo'] = 'bar' from '/path/to/src.yaml'>


    ..  attribute:: update

        Callable object that represent current update action.  By default
        is equal to :meth:`default_update`.

    """

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

    def __call__(self):
        """ Calls :attr:`update`, i.e. performs update action """
        self.update(self)

    def __repr__(self):
        return "<tree[{0._key!r}] = {0._value!r} from {0.source!r}>".format(self)

    def promise(self, deferred):
        """
        Helper method that wraps ``deferred`` callable by try-except block.
        It adds ``self`` as a first argument to any exception that might
        be raised from ``deferred``.  So that the exception will contain
        information of what expression from which file is caused it.

        :param callable deferred: Callable object that should be wrapped by
                                  :class:`Promise`

        """

        def wrapper():
            try:
                return deferred()
            except Exception as e:
                args = e.args + (self,)
                raise e.__class__(*args)

        return Promise(wrapper)

    @staticmethod
    def default_update(action):
        """
        Default value of :attr:`update`.  Literally performs:

        ..  code-block:: python

            action.tree[action.key] = action.value

        :param UpdateAction action: Current action object

        """
        action.tree[action.key] = action.value


class Promise(object):
    """
    Represents deferred expression that should be calculated at the end
    of loading process.  See :func:`resolve`, :meth:`Updater.eval_value`,
    :meth:`Updater.format_value`, :meth:`Updater.printf_value`, and
    :meth:`PostProcessor.resolve_promise`.

    :param callable deferred: Deferred expression

    """

    def __init__(self, deferred):
        self.deferred = deferred

    def __call__(self):
        """ Resolves deferred value, i.e. calls it and returns its result """
        return self.deferred()

    @staticmethod
    def resolve(value):
        """
        Helper method that resolves passed promises and returns their results.
        Other values are returned as is.

        :param value: Value to resolve
        :returns: Resolved promise or value as it is.

        ..  code-block:: pycon

            >>> Promise.resolve(Promise(lambda: 1))
            1
            >>> Promise.resolve(2)
            2

        """
        if isinstance(value, Promise):
            return value()
        return value


class ResolverProxy(object):
    """
    Helper object that wraps :class:`configtree.tree.Tree` objects.

    It pass each extracted value through :func:`resolve`, so that one
    deferred expression (see :class:`Promise`) can use another.

    If ``source`` argument is not ``None``, there will be ``__file__`` and
    ``__dir__`` keys available.

    :param Tree tree: Tree object to wrap
    :param str source: Path to source file

    ..  code-block:: pycon

        >>> tree = Tree()
        >>> proxy = ResolverProxy(tree, '/path/to/src.yaml')
        >>> tree['foo'] = Promise(lambda: 1)
        >>> tree['bar'] = Promise(lambda: proxy['foo'] + 1)
        >>> proxy['foo']
        1
        >>> proxy['bar']
        2
        >>> proxy['__file__']
        '/path/to/src.yaml'
        >>> proxy['__dir__']
        '/path/to'

    """

    def __init__(self, tree, source=None):
        self.__tree = tree
        self.__source = source

    def __getitem__(self, key):
        try:
            return Promise.resolve(self.__tree[key])
        except KeyError:
            if self.__source is not None:
                if key == "__file__":
                    return self.__source
                elif key == "__dir__":
                    return os.path.dirname(self.__source)
            raise

    def __getattr__(self, attr):
        return getattr(self.__tree, attr)


class Required(object):
    """
    Helper object that indicates undefined required key.

    Values of the type are set up by :meth:`Updater.required_value`
    and treated as error by :meth:`PostProcessor.check_required`.

    """

    def __init__(self, key, comment=""):
        self.key = key
        self.comment = comment

    def __repr__(self):
        result = "Undefined required key <%s>" % self.key
        if self.comment:
            result += ": " + self.comment
        return result


###############################################################################
# Post Processor
##


class PostProcessor(Pipeline):
    """
    Post processor is used by :class:`Loader` to perform final transformations
    of its result tree object after loading process is finished.

    Post processor iterates over passed :class:`configtree.tree.Tree` object
    and pass its keys and values through :attr:`__pipeline__`.  If any worker
    of the pipeline returns non ``None`` value, this value will be treated
    as an error.  Such errors are accumulated and raised within
    :class:`ProcessingError` exception at the end of processing.

    ..  attribute:: __pipeline__

        The list of workers is:
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
            raise ProcessingError(*errors)

    @Pipeline.worker(30)
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

    @Pipeline.worker(50)
    def check_required(self, tree, key, value):
        """
        Worker that checks tree for raw :class:`Required` values.

        :param Tree tree: Current processing tree
        :param str key: Current traversing key
        :param value: Current traversing value
        :returns: * passed ``value``, if it is an an instance of
                    :class:`Required`;
                  * ``None`` for other values.

        ..  attribute:: __priority__ = 50

        """
        if isinstance(value, Required):
            return value


class ProcessingError(Exception):
    """ Exception that will be raised, if post processor gets any error """
