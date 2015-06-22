Getting Started
===============

The following tutorial demonstrates basic usage of ConfigTree command line
utility program ``configtree``.  It covers all features, but does not explain
them in details.  It is enough to start using ConfigTree within your project,
however more detailed explanation will be given in the next section.

The following example available at ``demo`` directory of `the sources`_.

.. _the sources: https://bitbucket.org/kr41/configtree/src


Installation
------------

There is nothing unusual, just use Pip_:

..  code-block:: bash

    $ pip install configtree

...or easy_install:

..  code-block:: bash

    $ easy_install configtree


.. _Pip: https://pip.pypa.io/en/stable/installing.html


Simple Usage In Several Environments
------------------------------------

Let's imagine that we develop a web service, which consists of two web
applications: frontend and REST API.  First of all, we need simple configs
for development and production environments.

Create a separate directory for configuration files:

..  code-block:: bash

    $ mkdir config
    $ cd config

...and a file with default settings ``defaults.yaml``:

..  code-block:: yaml

    api:
        host: null
        port: 80
        db:
            driver: mysql
            user: null
            password: null
            name: demo_db
        secret: null
        logging: error
    frontend:
        host: null
        port: 80
        js:
            merge: yes
            minify: yes
        css:
            merge: yes
            minify: yes
        templates:
            reload: no
            cache: yes
        logging: error

If you run ``configtree`` command in the directory, you will get the following
output:

..  code-block:: bash

    $ configtree
    {
        "api.db.driver": "mysql",
        "api.db.name": "demo_db",
        "api.db.password": null,
        "api.db.user": null,
        "api.host": null,
        "api.logging": "error",
        "api.port": 80,
        "api.secret": null,
        "frontend.css.merge": true,
        "frontend.css.minify": true,
        "frontend.host": null,
        "frontend.js.merge": true,
        "frontend.js.minify": true,
        "frontend.logging": "error",
        "frontend.port": 80,
        "frontend.templates.cache": true,
        "frontend.templates.reload": false
    }

Let's create production and development configuration files that will override
some of the default settings.

Here are the production settings ``env-prod.yaml``:

..  code-block:: yaml

    api:
        host: api.example.com
        db:
            user: demo_user
            password: pa$$w0rd
    frontend:
        host: www.example.com

...and the development ones ``env-dev.yaml``:

..  code-block:: yaml

    api:
        host: localhost
        port: 5001
        db:
            user: root
            password: qwerty
    frontend:
        host: localhost
        port: 5000

But it is not enough.  We also should tell ``configtree`` how to load
these files.  In other words, we should provide an environment name.
Using an environment variable is a good option.  So let's name it ``ENV_NAME``.
To make ``configtree`` use this variable, we should create its own configuration
file ``loaderconf.py``.  It is a simple python module:

..  code-block:: python

    import os
    from configtree import make_walk

    walk = make_walk(env=os.environ['ENV_NAME'])

Here we make ``walk`` function, which will be used by loader to get list of
files to load.  We use :func:`configtree.loader.make_walk` factory function,
that accepts an environment name from variable ``ENV_NAME``.  So now, we
can load configuration using the following command:

..  code-block:: bash

    $ ENV_NAME=dev configtree
    {
        "api.db.driver": "mysql",
        "api.db.name": "demo_db",
        "api.db.password": "qwerty",
        "api.db.user": "root",
        "api.host": "localhost",
        "api.logging": "error",
        "api.port": 5001,
        "api.secret": null,
        "frontend.css.merge": true,
        "frontend.css.minify": true,
        "frontend.host": "localhost",
        "frontend.js.merge": true,
        "frontend.js.minify": true,
        "frontend.logging": "error",
        "frontend.port": 5000,
        "frontend.templates.cache": true,
        "frontend.templates.reload": false
    }

Of course, you can write your own ``walk`` function within ``loaderconf.py``
file to use your own algorithm to walk over the files to load.


Tree-like Environments
----------------------

Let's go deeper in the example.  Since our imaginable project consists
of two applications, our team will be divided into two sub-teams.  First one
will work on the backend API, and the second one will work on the frontend.
And they will definitely need slightly different configurations.  For instance,
backend team will want to set up debug level of logging on the backend,
but not on the frontend, and vice versa.

Make a directory for development environment settings:

..  code-block:: bash

    $ mkdir env-dev

Move ``env-dev.yaml`` file into the directory and rename it to ``common.yaml``.
It will store common development settings for both teams:

..  code-block:: bash

    $ mv env-dev.yaml dev-env/common.yaml

Then create two files ``env-frontend.yaml`` and ``env-api.yaml`` with the
following contents:

..  code-block:: yaml

    # env-frontend.yaml
    frontend.logging: debug

    # env-api.yaml
    api.logging: debug

Your ``configs`` directory should look like this::

    configs/
        env-dev/
            common.yaml
            env-frontend.yaml
            env-api.yaml
        defaults.yaml
        env-prod.yaml
        loaderconf.py

Now run the following command:

..  code-block:: bash

    $ ENV_NAME=dev.api configtree
    {
        "api.db.driver": "mysql",
        "api.db.name": "demo_db",
        "api.db.password": "qwerty",
        "api.db.user": "root",
        "api.host": "localhost",
        "api.logging": "debug",
        "api.port": 5001,
        "api.secret": null,
        "frontend.css.merge": true,
        "frontend.css.minify": true,
        "frontend.host": "localhost",
        "frontend.js.merge": true,
        "frontend.js.minify": true,
        "frontend.logging": "error",
        "frontend.port": 5000,
        "frontend.templates.cache": true,
        "frontend.templates.reload": false
    }

And the result will contain development settings for the backend team.

As you can see, environments can be organized in tree-like structure
with common settings at the root, and more specific ones at the leafs.


Post-processing and Validation
------------------------------

When we create the first file with default settings, there was a lot of ``null``
values.  Null itself is useless value in the configuration, but it can be
used as a remainder---environment configuration should override the value.
Let's make them required and raise errors, when result configuration contains
``null`` value.

Add the following code into ``loaderconf.py``:

..  code-block:: python

    def postprocess(tree):
        for key, value in tree.items():
            if value is None:
                raise ValueError('Missing required value "%s"' % key)

Now, if you run ``configtree`` command, you will get an error:

..  code-block:: pycon

    Traceback (most recent call last):
      ...
    ValueError: Missing required value "api.secret"

In this way, you will never deploy application using weak secret cryptographic
key on production server.

Since ``postporcess`` functions accepts the whole result tree of configuration,
you can also transform it as you want to, not only validate it.


Templates and Expressions
-------------------------

There is a common task of configuration handling, where we need to calculate
some settings using other ones.  So ConfigTree provides such feature.
Obviously, the feature strongly depends of loading order.  ConfigTree preserves
order of settings within single file.  In other words, it behaves exactly as
a regular program---all values defined before template is available in it.
Loading order of files depends on ``walk`` function.  See description
of :func:`configtree.loader.make_walk` for details of built-in ``walk`` loading
order.

Let's add some templates to our example.  For instance, URL map of API methods,
where each URL should include host name and port.  The map should be defined
in the default settings, because it does not depend on environment.  But it
should be defined when environment specific files have been already loaded,
because host name and port are overridden within the files.  Standard ``walk``
function provide special case for such purposes.  We should prefix our file
by ``final-`` prefix, so that it will be processed after ``env-`` prefixed
files.

Create file ``final-common.yaml`` with the following contents:

..  code-block:: yaml

    api.endpoints:
        index: "$>> http://{self[api.host]}:{self[api.port]}"
        login: "$>> {branch[index]}/login"
        logout: "$>> {branch[index]}/logout"

And run the following command:

..  code-block:: bash

    $ ENV_NAME=dev.frontend configtree
    {
        "api.db.driver": "mysql",
        "api.db.name": "demo_db",
        "api.db.password": "qwerty",
        "api.db.user": "root",
        "api.endpoints.index": "http://localhost:5001",
        "api.endpoints.login": "http://localhost:5001/login",
        "api.endpoints.logout": "http://localhost:5001/logout",
        "api.host": "localhost",
        "api.logging": "error",
        "api.port": 5001,
        "api.secret": "secret",
        "frontend.css.merge": true,
        "frontend.css.minify": true,
        "frontend.host": "localhost",
        "frontend.js.merge": true,
        "frontend.js.minify": true,
        "frontend.logging": "debug",
        "frontend.port": 5000,
        "frontend.templates.cache": true,
        "frontend.templates.reload": false
    }

As you can see, string values prefixed by ``$>>`` (with the trailing space) are
handled as templates.  Templates work using standard Python :meth:`str.format`
method.  There are two values available in template: ``self`` and ``branch``.
The first one is whole configuration tree object, the second one is a branch,
where the template is defined.

However, template sometimes is not enough.  For more complex cases, you can
use expressions.  Let's add a path to the project root directory, i.e. the
directory where ``configs`` is placed (it can be useful to calculate path to
the frontend assets, for instance).  ConfigTree loader add special keys for each
file it is processing: ``__file__`` and ``__dir__``.  The first one is full path
to the current file, the second one is for the current directory.  So that, to
get the root directory we can use :func:`os.path.dirname` function from
Python standard library.

To be able to use it, we should provide it to the loader.  Edit your
``loaderconf.py`` file:

..  code-block:: python

    import os
    from configtree import make_walk, make_update

    update = make_update(namespace={'os': os})      # Now we can use ``os`` within expressions
    walk = make_walk(env=os.environ['ENV_NAME'])

    def postprocess(tree):
        for key, value in tree.items():
            if value is None:
                raise ValueError('Missing required value "%s"' % key)

...and add the following line into ``defaults.yaml``:

..  code-block:: yaml

    root: ">>> os.path.dirname(self['__dir__'])"

And test it:

..  code-block:: bash

    $ ENV_NAME=dev.frontend configtree
    {
        "api.db.driver": "mysql",
        "api.db.name": "demo_db",
        "api.db.password": "qwerty",
        "api.db.user": "root",
        "api.endpoints.index": "http://localhost:5001",
        "api.endpoints.login": "http://localhost:5001/login",
        "api.endpoints.logout": "http://localhost:5001/logout",
        "api.host": "localhost",
        "api.logging": "error",
        "api.port": 5001,
        "api.secret": "secret",
        "frontend.css.merge": true,
        "frontend.css.minify": true,
        "frontend.host": "localhost",
        "frontend.js.merge": true,
        "frontend.js.minify": true,
        "frontend.logging": "debug",
        "frontend.port": 5000,
        "frontend.templates.cache": true,
        "frontend.templates.reload": false,
        "root": "/full/path/to/your/project"
    }

As you can see, stings prefixed by ``>>>`` is handled like regular Python
expressions.  To be able to use other names than Python built-ins, you should
provide ``namespace`` with such names to :func:`configtree.loader.make_update`
factory.  See its description, for other features.

Of course, you can implement your own ``update`` function to add your own
syntax sugar.


Using Within Shell Scripts
--------------------------

By default ``configtree`` command outputs the whole configuration in JSON
format.  You can specify ``--branch`` or ``-b`` option, to get only a portion
of the configuration.  You can also specify an output format using ``--format``
or ``-f`` option.  For instance, to get only database settings in shell script
format, use the following command:

..  code-block:: bash

    $ ENV_NAME=dev configtree -b api.db -f shell
    DRIVER='mysql'
    NAME='demo_db'
    PASSWORD='qwerty'
    USER='root'

Such format can be used within a shell script in the following way:

..  code-block:: bash

    # Setup environment
    ENV_NAME=dev

    # Import configuration
    eval "$( configtree -b api.db -f shell )"

    # Create backup of database
    if [[ "$DRIVER" == "mysql" ]]
    then
        mysqldump --user="$USER" --password="$PASSWORD" "$NAME" > dump.sql
    fi


Using With non-Python Programs
------------------------------

Since JSON parsers available for almost all programming languages, you can
use ``configtree`` command-line utility to build configuration as a part of
your build or/and deploy routine.

..  code-block:: bash

    # Setup environment
    ENV_NAME=dev

    # Build configuration
    configtree /path/to/config_dir > config.json

    # Build application
    # ...

There are two JSON converters available.  A condensed one is default converter
that is used by ``configtree`` program.  It returns flat structure as you can
see in the examples above:

..  code-block:: bash

    $ ENV_NAME=dev.frontend configtree
    {
        "api.db.driver": "mysql",
        "api.db.name": "demo_db",
        "api.db.password": "qwerty",
        "api.db.user": "root",
        "api.endpoints.index": "http://localhost:5001",
        "api.endpoints.login": "http://localhost:5001/login",
        "api.endpoints.logout": "http://localhost:5001/logout",
        "api.host": "localhost",
        "api.logging": "error",
        "api.port": 5001,
        "api.secret": "secret",
        "frontend.css.merge": true,
        "frontend.css.minify": true,
        "frontend.host": "localhost",
        "frontend.js.merge": true,
        "frontend.js.minify": true,
        "frontend.logging": "debug",
        "frontend.port": 5000,
        "frontend.templates.cache": true,
        "frontend.templates.reload": false
    }

A rare JSON converter returns the same structure as:

..  code-block:: bash

    $ ENV_NAME=dev.frontend configtree --format=rare_json
    {
        "api": {
            "db": {
                "driver": "mysql",
                "name": "demo_db",
                "password": "qwerty",
                "user": "root"
            },
            "endpoints": {
                "index": "http://localhost:5001",
                "login": "http://localhost:5001/login",
                "logout": "http://localhost:5001/logout"
            },
            "host": "localhost",
            "logging": "error",
            "port": 5001,
            "secret": "secret"
        },
        "frontend": {
            "css": {
                "merge": true,
                "minify": true
            },
            "host": "localhost",
            "js": {
                "merge": true,
                "minify": true
            },
            "logging": "debug",
            "port": 5000,
            "templates": {
                "cache": true,
                "reload": false
            }
        }
    }


Using Within Python Programs
----------------------------

If you use Python, you will be able to get all features of :class:`configtree.tree.Tree`
configuration storage in your code.  You don't have to create ``loaderconf.py``
module.  Instead, you can use :func:`configtree.loader.load` function directly:

..  code-block:: python

    import os
    from configtree import load, make_walk

    walk = make_walk(env=os.environ['ENV_NAME'])

    config = load('path/to/config_dir', walk=walk)

However, if you have ``loaderconf.py`` module, you can easily read it using
:func:`configtree.loader.loaderconf` function:

..  code-block:: python

    from configtree import load, loaderconf

    path = 'path/to/config_dir'
    config = load(path, **loaderconf(path))
