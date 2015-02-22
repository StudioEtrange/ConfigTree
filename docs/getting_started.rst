Getting Started
===============

The following tutorial demonstrates basic usage of ConfigTree command line
utility program ``configtree``.  It covers all features, but does not explain
them in details.  It is enough to start using ConfigTree within your project,
however more detailed explanation will be given in the next section.


Installation
------------

There is nothing unusual, just use Pip:

..  code-block:: bash

    $ pip install configtree

...or easy_install:

..  code-block:: bash

    $ easy_install configtree


Simple Usage In Several Environments
------------------------------------

Let's imagine that we develop a web service, which consists of two web
applications: frontend and REST API.  First of all, we need simple configs
for development and production environments.

Create a separate directory for configuration files:

..  code-block:: bash

    $ mkdir config
    $ cd config

...and file with default settings ``defaults.yaml``:

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
some of default settings.

Production one in the file ``env-prod.yaml``:

..  code-block:: yaml

    api:
        host: api.example.com
        db:
            user: demo_user
            password: pa$$w0rd
    frontend:
        host: www.example.com

And development one in the file ``env-dev.yaml``:

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

If you run ``configtree`` command, you will get the same output as before.
It happens, because we have not provided environment name to loader yet.
So let's do that.  Create ``loaderconf.py`` file with the following contents:

..  code-block:: python

    import os
    from configtree import make_walk

    walk = make_walk(env=os.environ['ENV_NAME'])

Here we make ``walk`` function, which will be used by loader to get list of
files to load.  We use :func:`configtree.loader.make_walk` factory function,
that accepts environment name from shell variable ``ENV_NAME``.  So now, we
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
will work on backend API, and the second one will work on frontend.  And they
will definitely need slightly different configurations.  For instance,
debug level of logging should be set up.

Make a directory for development environment settings:

..  code-block:: bash

    $ mkdir env-dev

Move ``env-dev.yaml`` file into the directory:

..  code-block:: bash

    $ mv env-dev.yaml dev-env/common.yaml

And create two files ``env-frontend.yaml`` and ``env-api.yaml`` with the
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

As you can see, environments can be organized in tree-like structure
with common settings at the root, and more specific ones at the leafs.


Post-processing and Validation
------------------------------

When we create the first file with default settings, there was a lot of ``null``
values.  Null itself is useless value in the configuration, but it can be
used as a remainder---environment configuration should override the value.
Let's make them required and raise errors, when result configuration contains
``null`` value.  Add the following code into ``loaderconf.py``:

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
of :func:`configtree.loader.make_walk` for details of built-in `walk` loading
order.

Let's add some templates to our example.  For instance, URL map of API methods,
where each URL should include host name and port.  The map should be defined
in the default settings, because it does not depend on environment.  But it
should be defined when environment specific files have been already loaded,
because host name and port are override within the files.  Standard ``walk``
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

As you can see, string values prefixed by ``$>>`` (with trailing space) are
handled as templates.  Templates work using standard Python :meth:`str.format`
method.  There are two values available in template: ``self`` and ``branch``.
The first one is whole configuration tree object, the second one is a branch,
where the template is defined.

However, template sometimes is not enough.  For more complex cases, you can
use expressions.  Let's add path to project root directory, i.e. the directory
where ``configs`` is placed (it can be useful to calculate path to frontend
assets, for instance).  ConfigTree loader add special keys for each file it is
processing: ``__file__`` and ``__dir__``.  The first one is full path to current
file, the second one is for current directory.  So that, to get root directory
we can use :func:`os.path.dirname` function from standard Python library.
To be able to use it, we should provide it to loader.

Edit your ``loaderconf.py`` file:

..  code-block:: python

    import os
    from configtree import make_walk, make_update

    update = make_update(namespace={'os': os})      # Now we can use ``os`` within expression
    walk = make_walk(env=os.environ['ENV_NAME'])

    def postprocess(tree):
        for key, value in tree.items():
            if value is None:
                raise ValueError('Missing required value "%s"' % key)

...and add the following line into ``defaults.yaml``:

..  code-block:: yaml

    root: ">>> os.path.dirname(self['__dir__'])"

Test it:

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
format.  You can specify ``--branch`` or ``-b`` option, to get only portion
of the configuration.  You can also specify an output format using ``--format``
or ``-f`` option.  For instance, to get only database settings in shell script
format, use the following command:

..  code-block:: bash

    $ ENV_NAME=dev configtree -b api.db -f shell
    DRIVER='mysql'
    NAME='demo_db'
    PASSWORD='qwerty'
    USER='root'

Such format can be used within shell script in the following way:

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
