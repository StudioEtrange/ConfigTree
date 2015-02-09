""" The module provides utility functions to load tree object from files """

import os
import re

from . import source
from .compat import string
from .tree import Tree, flatten


def load(path, walk=None, update=None, tree=None):
    """
    Loads :class:`configtree.tree.Tree` object from files.

    A `path` argument should be a path to directory containing files to load.

    A `walk` argument, if provided should be callable, which accepts `path`
    argument and returns an iterator over the files to load.  By default,
    a function constructed by :func:`make_walk` is used.

    An `update` argument, if provided should be a callable, which accepts three
    arguments `tree`, `key`, `value` and performs update of `tree` using
    `key` and `value` pair.  By default, a function constructed by
    :func:`make_update` is used.

    A `tree` argument, if provided should be a tree-like object, which will
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
                update(tree, key, value)
            del tree['__file__']
            del tree['__dir__']
    return tree


def make_walk(env=''):
    """
    Constructs `walk` function, which will be used by :func:`load` one.

    The `walk` function recursively iterates over the directory and yields
    files to load.  It will skip:

        *   file, if its extension is not contained in the map of
            :mod:`configtree.source`.
        *   file or directory, if its name starts with "_" underscore char;
        *   file or directory, if its name starts with "env-" and the rest
            part of the name does not match environment name specified by
            the `env` argument.

    The files are emitted in the following order:

        1.  Top level common files.
        2.  Common files contained in the nested directories.
        3.  Environment specific files.
        4.  Files contained in the environment specific directories.

    All files are also sorted using natural sort within their groups.

    The environment is specified by `env` argument.  It supports tree-like
    environment configuration.  For instance, you have the following
    environments: `dev` (developer's one), `test.staging` (for staging server),
    `test.stress` (for stress testing), and `prod` (for production usage).
    Configuration files may be organized in the following way::

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

    So that, specifying `env` argument as `test.staging`, will emit the
    following files::

        config/common/common-config.yaml
        config/env-test/common-test-config.yaml
        config/env-test/env-staging/staging-server-config.yaml

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
            for f in walk(d, env):
                yield f
        for f in sorted(env_files):
            yield f
        for d in sorted(env_dirs):
            for f in walk(d, tail):
                yield f

    return walk


def make_update(namespace=None):
    """
    Constructs `update` function, which will be used by :func:`load`.

    The `update` function adds a pinch of syntactic sugar to loading
    `configtree.tree.Tree` object from files:

    ..  code-block:: yaml

        x:
            a: 1
            b: 2
        y:
            b: 3

            # If string value starts with ">>> ", it will be evaluated
            # as Python expression. Where `branch` name refers to the current
            # tree branch, `tree` name refers to the whole tree object.
            # Additionally, names passed via `namespace` argument can be
            # used within expression.
            c: ">>> tree['x.a'] + branch['b']"               # c == 4

            # If string value starts with "$>> ", it will be used as a template
            # string.  It will be formatted used standard `format` method.
            # Only `branch` and `tree` names are available within formatting.
            d: "$>> {tree[x.a]} + {branch[b]} = {branch[c]}" # d == "1 + 3 = 4"

            # If key ends with "?", the corresponding value will be set
            # only if the key does not exists in the tree.  It is useful
            # to set default values, which could be already set within
            # another file.
            e: [1, 2]
            e?: []                                           # e == [1, 2]
            f?: []                                           # f == []

            # If key contains "#", the part after that char will be used
            # as method name.  This method will be called using the value.
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
