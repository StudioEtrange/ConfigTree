Getting Started
===============

The following tutorial demonstrates basic usage of ConfigTree.
It covers all features, but does not explain them in details.
It is enough to start using ConfigTree within your project,
however more detailed explanation will be given in the :ref:`next section <advanced_usage>`.


Installation
------------

There is nothing unusual, just use Pip_:

..  code-block:: bash

    $ pip install configtree

.. _Pip: https://pip.pypa.io/en/stable/installing.html


Warming up
----------

Let's create a separate directory, for our experiments:

..  code-block:: bash

    $ mkdir configs
    $ cd configs

Then create some dummy data:

..  code-block:: bash

    $ touch test.yaml
    $ echo "x.y: 1" >> test.yaml
    $ echo "x:" >> test.yaml
    $ echo "  z: 2" >> test.yaml

The test file should look like this:

..  code-block:: yaml

    x.y: 1
    x:
      z: 2

Now, let's run :ref:`ctdump` to see how it loads our file:

..  code-block:: bash

    $ ctdump json
    {"x.z": 2, "x.y": 1}

Let's play with its arguments:

..  code-block:: bash

    $ ctdump json --json-indent=4 --json-sort
    {
        "x.y": 1,
        "x.z": 2
    }
    $ ctdump json --json-indent=4 --json-sort --json-rare
    {
        "x": {
            "y": 1,
            "z": 2
        }
    }

And finally, let's load the file within Python code and fiddle with the result:

..  code-block:: pycon

    >>> from configtree import Loader
    >>> load = Loader()
    >>> tree = load('.')
    >>> tree
    Tree({'x.y': 1, 'x.z': 2})
    >>> tree['x']
    BranchProxy('x'): {'z': 2, 'y': 1}
    >>> tree['x.y']
    1
    >>> tree == {'x.y': 1, 'x.z': 2}
    True
    >>> tree['x'] == {'y': 1, 'z': 2}
    True

You can see that:

*   ConfigTree flattens the file on loading, i.e. there is no difference between
    dot-separated keys and nested mappings:

    ..  code-block:: yaml

        # This is identical...
        x.y: 1
        x.z: 2

        # ...to this
        x:
            y: 1
            z: 2

    See :func:`configtree.tree.flatten` for details.

*   ConfigTree uses :class:`configtree.tree.Tree` to store the result.
    This class provides dictionary interface and can be used wherever
    built-in :class:`dict` is expected.  It also provides ability to get
    branches, i.e. expose intermediate keys.  That is why it named "Tree".

*   :class:`configtree.loader.Loader` is used to load :class:`configtree.tree.Tree`
    object from files.  The following tutorial is devoted to its features.

*   :ref:`ctdump` can be used to dump tree into JSON, so it can be useful
    to build configuration for programs written in other programming languages.

Now remove the test file and move on to the real world example.


Safe defaults
-------------

Let's imagine that we develop a web service, which consists of two web
applications: frontend and REST API.  First of all, we need simple configurations
for development and production environments.  These two configurations
will have lots of common parameters.  So it will be better to create a
default configuration, that should be updated by environment-specific options.

However, the default configuration must contain safe default parameters.
Because it is always possible that someone forget to override default value
in the production environment.  Nobody wants to go live with weak cryptographic
keys, for instance.

Using ConfigTree it is possible to mark keys as required.  So the loader
will raise an error, if such keys have not been overridden.

Create ``default.yaml`` with the following content:

..  code-block:: yaml

    api:                                            # API configuration
        host: "!!! API host name"
        port: 80
        db:
            driver: "mysql"
            user: "!!!"
            password: "!!!"
            name: "demo_db"
        secret: "!!! Web tokens encryption key"
        logging: "error"
    frontend:                                       # Frontend configuration
        host: "!!! Frontend host name"
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
        logging: "error"

Now let's test it:

..  code-block:: bash

    $ ctdump json
    configtree [ERROR]: Undefined required key <api.db.password>
    configtree [ERROR]: Undefined required key <api.db.user>
    configtree [ERROR]: Undefined required key <api.host>: API host name
    configtree [ERROR]: Undefined required key <api.secret>: Web tokens encryption key
    configtree [ERROR]: Undefined required key <frontend.host>: Frontend host name

As you can see, the loader reports error for each key, marked with "!!!".
If you run loader programmatically, an exception of :class:`configtree.loader.ProcessingError`
will be raised.

Move on and see how to override the values in the environment-specific
configuration.


Loading environment-specific configuration
------------------------------------------

Let's create production configuration in file ``env-prod.yaml`` with the following
content:

..  code-block:: yaml

    api:
        host: "api.example.com"
        db:
            user: "demo_user"
            password: "pa$$w0rd"        # Password must be strong
        secret: "s3cre7"                # As well as cryptographic key :)
    frontend:
        host: "www.example.com"

Now we should "say" to the loader to load this file only in the production environment.
The part of loader that responds to get list of files to load is :ref:`Walker`.
To change its default behavior, we should manually create :class:`configtree.loader.Walker`
object and pass it into :class:`configtree.loader.Loader`:

..  code-block:: pycon

    >>> from configtree import Loader, Walker
    >>> walk = Walker(env='prod')
    >>> load = Loader(walk=walk)

To make it work in :ref:`ctdump`, create :ref:`loaderconf_py` file with
the following content:

..  code-block:: python

    import os

    from configtree import Walker

    walk = Walker(env=os.environ['ENV_NAME'])

And test it:

..  code-block:: bash

    $ ENV_NAME=prod ctdump json
    {...}


Using hierarchical environments
-------------------------------

Now let's think about development environments.  Our imaginable project
consists of two parts: API and frontend.  So our imaginable team should
consist of two sub-teams: API developers and frontend developers.

The frontend team does not care about backend logs, but they want to have debug
logging level on frontend.  They also work on templates, and want to
switch off caching and switch on reloading options, and so on.  While the backend
team needs slightly different configuration.

So let's create a directory for development configuration with three files::

    env-dev/                    # Development configuration directory
        common.yaml             # Common development options
        env-api.yaml            # API team development options
        env-frontend.yaml       # Frontend team development options

And play with ``ENV_NAME``.  Here we use ``--verbose`` option of :ref:`ctdump`
to get list of loaded files:

..  code-block:: bash

    $ ENV_NAME=dev ctdump json --verbose
    configtree [INFO]: Walking over "/path/to/configs"
    configtree [INFO]: Loading "defaults.yaml"
    configtree [INFO]: Loading "env-dev/common.yaml"

    $ ENV_NAME=dev.api ctdump json --verbose
    configtree [INFO]: Walking over "/path/to/configs"
    configtree [INFO]: Loading "defaults.yaml"
    configtree [INFO]: Loading "env-dev/common.yaml"
    configtree [INFO]: Loading "env-dev/env-api.yaml"

    $ ENV_NAME=dev.frontend ctdump json --verbose
    configtree [INFO]: Walking over "/path/to/configs"
    configtree [INFO]: Loading "defaults.yaml"
    configtree [INFO]: Loading "env-dev/common.yaml"
    configtree [INFO]: Loading "env-dev/env-frontend.yaml"

As you can see, environments can be organized in hierarchy, where the most
common configuration options are defined at the root, and the most specific—at the leafs.


Templates and evaluable expressions
-----------------------------------

Sometimes you need to calculate some values in your configuration.

For example, let's add some endpoint URLs to the API configuration.
Edit ``default.yaml`` file and add the following:

..  code-block:: yaml

    api:
        # Previously added API configuration goes here
        endpoints:
            index: "%>> http://%(api.host)s:%(api.port)s"
            login: "%>> %(api.endpoints.index)s/login"
            logout: "%>> %(api.endpoints.index)s/logout"
    frontend:
        # Previously added frontend configuration goes here

In the result production configuration it will look like this:

..  code-block:: json

    {
        "api": {
            "endpoints": {
                "index": "http://api.example.com:80",
                "login": "http://api.example.com:80/login",
                "logout": "http://api.example.com:80/logout"
            }
        }
    }

Such expressions are calculated after whole configuration has been loaded.
So you can use values that are defined after the expression, or even defined
in another file.

You can also use expressions similar to standard Python console.  And even
add your own syntactic sugar.  See :ref:`updater` and :ref:`postprocessor`
sections of the manual for details.
