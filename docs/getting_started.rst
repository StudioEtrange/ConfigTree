Getting Started
===============

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

...and file with default settings ``config/defaults.yaml``:

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

Let's go deeper in the example above.  Since our imaginable project consists
of two applications, our team will be divided into two sub-teams.  First one
will work on backend API, and the second one will work on frontend.  And they
will definitely need slightly different configurations.  For instance,
debug level of logging should be set up.

Make a directory for development environment settings:

..  code-block:: bash

    $ mkdir configs/env-dev

Move ``env-dev.yaml`` file into the directory:

..  code-block:: bash

    $ mv configs/env-dev.yaml configs/dev-env/common.yaml

And create two files ``env-frontend.yaml`` and ``env-api.yaml`` with the
following contents:

..  code-block:: yaml

    # env-frontend.yaml
    frontend.logging: debug

    # env-frontend.yaml
    api.logging: debug

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

As you can see, environments can be organized in the tree-like structure
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

