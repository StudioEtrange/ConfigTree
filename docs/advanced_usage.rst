.. _advanced_usage:

Advanced Usage
==============


Loading Overview
----------------

The loading of configuration is done in the following steps.

1.  :ref:`Get the list of files to load <walker>`.
2.  :ref:`Load data from each file <source>`.
3.  :ref:`Put the data into result tree object <updater>`.
4.  :ref:`Post-process the result object <postprocessor>`.
5.  :ref:`Format the result object <formatter>`.

The loading itself is done by :class:`configtree.loader.Loader`.  It performs
first four steps.  If you use :class:`configtree.loader.Loader` programmatically,
it is probably what you need.  The last fifth step is performed by :ref:`ctdump`
before printing the result.


.. _walker:

Walker
------

:class:`configtree.loader.Walker` object is used to get list of files to load.
The walker responds for skipping ignored and unsupportable files, and sort
the rest of ones by their priority.

To pass walker into :class:`configtree.loader.Loader` programmatically use:

..  code-block:: python

    from configtree import Loader, Walker

    load = Loader(walk=Walker())

To specify walker for :ref:`ctdump`, create ``walk`` object in :ref:`loaderconf_py`

..  code-block:: python

    from configtree import Walker

    walk = Walker()


Unsupportable and ignored files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The walker skips file, if its name starts with underscore or dot chat;
or its extension is not in :data:`configtree.source.map`,
i.e. there is no loader for the file format.


Environment specific files and directories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Additionally, the walker can skip or include environment specific files.
The name of environment specific file (or directory) starts with ``env-`` prefix.
The rest part of the name is considered as an environment name.  To control
what to include, pass ``env`` argument into :class:`configtree.loader.Walker`
constructor.

For example, here is the directory of configuration::

    configs/
        defaults.yaml           # Default configuration
        env-dev/
            defaults.yaml       # Default developing configuration
            env-john.yaml       # John's personal configuration
            env-jane.yaml       # Jane's personal configuration
        env-prod.yaml           # Production configuration

This is how we can get files of different environments:

..  code-block:: pycon

    >>> walk = Walker(env='prod')       # Production configuration
    >>> for path in walk('./configs'): print(path)
    /full/path/to/configs/defaults.yaml
    /full/path/to/configs/env-prod.yaml

    >>> walk = Walker(env='dev')        # Default developing configuration
    >>> for path in walk('./configs'): print(path)
    /full/path/to/configs/defaults.yaml
    /full/path/to/configs/env-dev/defaults.yaml

    >>> walk = Walker(env='dev.john')   # John's personal developing configuration
    >>> for path in walk('./configs'): print(path)
    /full/path/to/configs/defaults.yaml
    /full/path/to/configs/env-dev/defaults.yaml
    /full/path/to/configs/env-dev/env-john.yaml


.. _walker-final-files:

Final files
~~~~~~~~~~~

If name of a file (or directory) starts with ``final`` sting, the file will be
placed at the end of result list of files.


.. _walker-order-of-files:

The order of files
~~~~~~~~~~~~~~~~~~

The result list of files is sorted in the following order:

1.  Regular file, priority ``30``.
2.  Regular directory, priority ``31``.
3.  Environment file, priority ``50``.
4.  Environment directory, priority ``51``.
5.  Final directory, priority ``100``.
6.  Final file, priority ``101``.

Additionally, files are alphabetically sorted within their groups.

For example, we got this configuration directory::

    configs/
        defaults.yaml
        common/
            foo.yaml
            bar.yaml
        env-dev/
            defaults.yaml
            env-john.yaml
            env-jane.yaml
        env-dev.yaml
        env-prod.yaml
        final/
            foo.yaml
            bar.yaml
        final-foo.yaml
        final-bar.yaml

If ``env`` is equal to ``dev.jane``, the files from the list above will be
returned in the following order::

    defaults.yaml           # Regular file
    common/bar.yaml         # Regular directory.  Regular file bar.yaml goes before foo.yaml,
    common/foo.yaml         # because of alphabetical sort.
    env-dev.yaml            # Environment file
    env-dev/defaults.yaml   # Regular file from environment directory
    env-dev/env-jane.yaml   # Environment file the same directory
    final/bar.yaml          # Regular file from final directory
    final/foo.yaml
    final-bar.yaml          # Final file
    final-foo.yaml


Extending walker
~~~~~~~~~~~~~~~~

If you want to add some features to the walker, you can subclass it and
add some additional workers to its pipeline (see :class:`configtree.loader.Pipeline`).

Each worker accepts single argument—:class:`configtree.loader.File` object,
and returns priority for the passed file.  ``None`` value means, that the
worker passes the file to the next worker.  ``-1`` value means, that the
file must be skipped.  Other means priority and is used to sort files in
the result list.

For example, let's add support of initial files as opposite of :ref:`final ones <walker-final-files>`,
that should be at the beginning of the result list.

..  code-block:: python

    from configtree import Walker, Pipeline

    class MyWalker(Walker):

        @Pipeline.worker(20)   # Place worker between ``ignored`` and ``final``
        def initial(self, fileobj):
            if not fileobj.name.startswith('init'):
                return None
            return 11 if fileobj.isdir else 10


.. _source:

Source
------

Loading data from files is done by :mod:`configtree.source` module.  The module
provides :data:`configtree.source.map` that stores map of file extensions to
loaders.  The map is used by :class:`configtree.loader.Loader` to load data
from files.  The following formats are supported out of the box:

*   YAML with extensions ``.yaml`` and ``.yml`` by :func:`configtree.source.from_yaml`;
*   JSON with extension ``.json`` by :func:`configtree.source.from_json`.

The map is filled scanning `entry points`_ ``configtree.source``.  So that it is
extensible by plugins.  Ad hoc loader can be also defined within :ref:`loaderconf_py`
module.  The loader itself should be a callable object, which accepts single
argument—opened file, and returns :class:`collections.OrderedDict`.

Example:

..  code-block:: python

    from collections import OrderedDict

    def from_xml(data):
        # Do something with ``data`` file
        return OrderedDict(...)

Define plugin within ``setup.py`` file:

..  code-block:: python

    entry_points="""\
    [configtree.source]
    .xml = plugin.module.name:from_xml
    """

Or define ad hoc loader within :ref:`loaderconf_py`:

..  code-block:: python

    from configtree import source

    source.map['.xml'] = from_xml

.. _entry points: https://pythonhosted.org/setuptools/setuptools.html
                  #dynamic-discovery-of-services-and-plugins


.. _updater:

Updater
-------

:class:`configtree.loader.Updater` object is used to put loaded data into
the result object of :meth:`configtree.loader.Loader.__call__` method.  The updater
responds for adding syntactic sugar into regular data that come from YAML,
JSON, and other files.

Updating process can be basically illustrated by the following code:

..  code-block:: python

    for key, value in loaded_data.items():
        # result_tree[key] = value

        # Instead of simple assignment above, we call updater.
        # So that extending updater, we can change the default behavior.
        updater(result_tree, key, value)

To pass updater into :class:`configtree.loader.Loader` programmatically use:

..  code-block:: python

    from configtree import Loader, Updater

    load = Loader(update=Updater())

To specify updater for :ref:`ctdump`, create ``update`` object in :ref:`loaderconf_py`

..  code-block:: python

    from configtree import Updater

    update = Updater()


Built-in syntactic sugar
~~~~~~~~~~~~~~~~~~~~~~~~

Out of the box the updater supports the following:

*   Setup default value, see :meth:`configtree.loader.Updater.set_default`:

    ..  code-block:: yaml

        x: 1
        x?: 2      # x == 1
        y?: 3      # y == 3

*   Add a value to the current value. If current value and the added value are number, a sum is used. 
    If it is a collection, the value is append to it otherwise the value and the current value are
    converted to string and concated together with a space character as separator.
    
    see :meth:`configtree.loader.Updater.add_method`:
    
    ..  code-block:: yaml

        bar: "string"                    # bar == "string"
        bar+: "other"                    # bar == "string other"
        foo: [1, 2]                      # foo == [1, 2]
        foo+: [5, 6]                     # foo == [1, 2, 5, 6]
        foo+: (7, "8")                   # foo == [1, 2, 5, 6, 7, "8"]
        foo+: "9"                        # foo == [1, 2, 5, 6, 7, "8", "9"]
        x: 5                             # x 5
        x+: 2     

*   Call specified method of the value, see :meth:`configtree.loader.Updater.call_method`:

    ..  code-block:: yaml

        x: [1, 2, 3]
        x#append: 4         # x == [1, 2, 3, 4]

*   Use the value as a template, see :meth:`configtree.loader.Updater.format_value` and
    :meth:`configtree.loader.Updater.printf_value`:

    ..  code-block:: yaml

        x: 1
        y:
            foo: 2

            # Formatted by ``str.format()``
            bar: "$>> {self[x]} {branch[foo]}"      # bar == '1 2'

            # Formatted by ``%``
            baz: "%>> %(x)s %(y.foo)s"              # baz == '1 2'

*   Evaluate expressions, see :meth:`configtree.loader.Updater.eval_value`

    ..  code-block:: python

        from os import path

        # Namespace will be passed into expressions
        update = Updater(namespace={'path': path})


    ..  code-block:: yaml

        configdir: ">>> self['__dir__']"
        projectdir: ">>> path.dirname(self['configdir'])"


*   Setup required values, see :meth:`configtree.loader.Updater.required_value`

    ..  code-block:: yaml

        x: "!!!"
        y: "!!! Add useful comment here"


Deferred expressions
~~~~~~~~~~~~~~~~~~~~

Formatting or evaluating value is replaced by :class:`configtree.loader.Promise` object.
The object stores callable object, that should be called after loading process
has been done.  So that all expressions are calculated on :ref:`post-processing step <postprocessor>`.


Extending updater
~~~~~~~~~~~~~~~~~

If you want to add some features to the updater, you can subclass it and
add some additional workers to its pipeline (see :class:`configtree.loader.Pipeline`).

Each worker accepts single argument—:class:`configtree.loader.UpdateAction` object.
Workers can transform :attr:`configtree.loader.UpdateAction.key`,
:attr:`configtree.loader.UpdateAction.value`, or
:attr:`configtree.loader.UpdateAction.update` attributes to change default
updating behavior.

For example, let's add support of some template language.

..  code-block:: python

    from configtree.loader import Updater, Pipeline, ResolverProxy

    class MyUpdater(Updater):

        @Pipeline.worker(75)   # Place worker after ``eval_value`` and ``required_value``
        def template_value(self, action):
            if not isinstance(action.value, string) or \
               not action.value.startswith('template>> '):
                return
            value = action.value[len('template>> '):].strip()
            action.value = action.promise(
                lambda: template(value, ResolverProxy(action.tree, action.source))
            )

Here we wrapped :class:`configtree.tree.Tree` object by :class:`configtree.loader.ResolverProxy`.
The proxy is helper object that resolves :class:`configtree.loader.Promise`
objects on fly.  So that the expression could use other deferred expressions.

We also create :class:`configtree.loader.Promise` object using
:meth:`configtree.loader.UpdateAction.promise`.  Because the method wraps
original expression by exception handler that adds useful debug info into
raised exceptions.


.. _postprocessor:

Post-processor
--------------

:class:`configtree.loader.PostProcessor` object is used to finalize
:class:`configtree.tree.Tree` object returned by :class:`configtree.loader.Loader`.
The post-processor responds for resolving deferred expressions (:class:`configtree.loader.Promise`)
and check for undefined required keys (:meth:`configtree.loader.Updater.required_value`).
It is a good place for custom validators, see :ref:`extending-postprocessor`.

To pass post-processor into :class:`configtree.loader.Loader` programmatically use:

..  code-block:: python

    from configtree import Loader, PostProcessor

    load = Loader(postprocess=PostProcessor())

To specify post-processor for :ref:`ctdump`, create ``postprocess`` object in :ref:`loaderconf_py`

..  code-block:: python

    from configtree import PostProcessor

    postprocess = PostProcessor()


.. _extending-postprocessor:

Extending post-processor
~~~~~~~~~~~~~~~~~~~~~~~~

If you want to add some features to the post-processor, you can subclass it and
add some additional workers to its pipeline (see :class:`configtree.loader.Pipeline`).

Each worker accepts three arguments: :class:`configtree.tree.Tree` object,
current processing ``key``, and ``value``.  It should return ``None``,
or error message as a string (or as an object that has human readable string representation).
These message will be accumulated and thrown within single :class:`configtree.loader.ProcessingError`
exception at the end of processing.

For example, let's add validator of port number values.  If ``key`` ends with ``.port``,
it must be ``int`` value greater than zero.

..  code-block:: python

    from configtree import PostProcessor, Pipeline

    class MyPostProcessor(PostProcessor):

        @Pipeline.worker(100)   # Place worker after ``check_required``
        def validate_port(self, tree, key, value):
            if not key.endswith('.port'):
                return None
            try:
                value = int(value)
            except ValueError:
                return (
                    '%s: type ``int`` is expected, but %r of type ``%s`` is given'
                    % (key, value, type(value).__name__)
                )
            if value < 0:
                return '%s: port number should be greater than zero, but %r is given' % value
            tree[key] = value

.. _formatter:

Formatter
---------

Formatting of :class:`configtree.tree.Tree` objects is done by :mod:`configtree.formatter` module.
The module provides :data:`configtree.formatter.map` that stores map of format names to
formatters.  This formatters are used by :ref:`ctdump` to print result.
The following formats are supported out of the box:

*   JSON with name ``json`` by :func:`configtree.formatter.to_json`;
*   Shell script (Bash) with name ``shell`` by :func:`configtree.formatter.to_shell`.

The map is filled scanning `entry points`_ ``configtree.formatters``.  So that it is
extensible by plugins.  Ad hoc formatter can be also defined within :ref:`loaderconf_py`
module.  The formatter itself should be a callable object, which accepts single
argument—:class:`configtree.tree.Tree` object, and returns string.  Optional
keyword arguments are possible too.  However, if you want to specify
these arguments via :ref:`ctdump`, you should use decorator :func:`configtree.formatter.option`.

Example:

..  code-block:: python

    from configtree import formatter

    @formatter.option(
        'indent', default=None, type=int, metavar='<indent>',
        help='indent size (default: %(default)s)'
    )
    def to_xml(tree, indent=None):
        # See ``demo/loaderconf.py`` for complete working code of the formatter
        result = ...  #  Do something with tree
        return result

Define plugin within ``setup.py`` file:

..  code-block:: python

    entry_points="""\
    [configtree.formatter]
    xml = plugin.module.name:to_xml
    """

Or define ad hoc formatter within :ref:`loaderconf_py`:

..  code-block:: python

    from configtree import formatter

    formatter.map['xml'] = to_xml

.. _entry points: https://pythonhosted.org/setuptools/setuptools.html
                  #dynamic-discovery-of-services-and-plugins


.. _ctdump:

``ctdump`` shell command
------------------------

Command line utility to load :class:`configtree.tree.Tree` objects and
dump them using available :ref:`formatters <formatter>`.

You can use it to build JSON files, that can be loaded by progams written
in any programming language, that supports parsing JSON.

..  code-block::  Bash

    # Somewhere in your build script
    ctdump json --path path/to/config/sources > path/to/build/config.json

You can build only a part of configuration specifying branch:

..  code-block::  Bash

    ctdump json --path path/to/config/sources --branch app.http > path/to/build/server.json
    ctdump json --path path/to/config/sources --branch app.db > path/to/build/database.json

The special formatter for shell scripts helps to use configuration within Bash scripts.
For example, you want to use database credentials:

..  code-block::  Bash

    backup_db() {
        eval "$( ctdump shell --branch app.db --shell-prefix 'local ' )"
        # Output of ctdump will look like this:
        #   local username='dbuser'
        #   local password='qwerty'
        #   local database='mydata'

        mysqldump --user="$username" --password="$password" "$database" > dump.sql
    }

To get full help of the command run:

..  code-block::  Bash

    ctdump --help


.. _loaderconf_py:

``loaderconf.py``
-----------------

The module is used to specify arguments for :class:`configtree.loader.Loader`.
It is placed at the root of configuration files, and usually used by :ref:`ctdump`
to create its loader by :meth:`configtree.loader.Loader.fromconf`.

It is also a good place for ad hoc :ref:`source loaders <source>` and :ref:`formatters <formatter>`.

Here is an example of the module:

..  code-block:: python


    import os

    from configtree import Walker, Updater
    from configtree import formatter

    # Create ``walk`` and ``update`` that will be used by ``Loader``.
    update = Updater(namespace={'os': os})
    walk = Walker(env=os.environ['ENV_NAME'])


    # Create ad hoc formatter
    @formatter.option(
        'indent', default=None, type=int, metavar='<indent>',
        help='indent size (default: %(default)s)'
    )
    def to_xml(tree, indent=None):
        """ Dummy XML formatter """

        def get_indent(level):
            if indent is None:
                return ''
            else:
                return ' ' * indent * level

        result = ['<configtree>']
        for key, value in tree.items():
            result.append('%s<item>' % get_indent(1))
            result.append('%s<key>%s</key>' % (get_indent(2), key))
            result.append(
                '%s<value type="%s">%s</value>' % (
                    get_indent(2),
                    type(value).__name__,
                    value,
                )
            )
            result.append('%s</item>' % get_indent(1))
        result.append('</configtree>')
        if indent is None:
            return ''.join(result)
        else:
            return os.linesep.join(result)

    formatter.map['xml'] = to_xml
