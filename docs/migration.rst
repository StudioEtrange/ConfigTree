Migration guide
===============


.. _migration03to04:

Migration from version 0.3 to 0.4
---------------------------------


.. _migration03to04-shell-commands:

Shell commands
~~~~~~~~~~~~~~

Shell command ``configtree`` is deprecated in favor of ``ctdump``.
The latter one uses new loader infrastructure and new formatters.

The following pairs of commands give the identical result:

..  code-block:: bash

    configtree
    ctdump json --json-sort --json-indent=4

    configtree --format json
    ctdump json --json-sort --json-indent=4

    configtree --format rare-json
    ctdump json --json-sort --json-indent=4 --json-rare

    configtree --format shell
    ctdump shell --shell-sort --shell-capitalize


``loaderconf.py``
~~~~~~~~~~~~~~~~~

The following functions are deprecated:

*   :func:`configtree.loader.make_walk` in favor of :class:`configtree.loader.Walker`;
*   :func:`configtree.loader.make_update` in favor of :class:`configtree.loader.Updater`;

Simple replacement gives the same result:

..  code-block:: python

    # This code...

    from configtree import make_walk, make_update

    walk = make_walk(envname)
    update = make_update(namespace)

    # ...should be replaced by this one
    # Take a notice, that positional arguments is not acceptable.
    # Use named ones.

    from configtree import Walker, Updater

    walk = Walker(env=envname)
    update = Updater(namespace=namespace)

Function ``postprocess`` should be created using class :class:`configtree.loader.PostProcessor`.
If there is no built-in features you need, consider extending of the class.

..  code-block:: python

    # This code...

    def postprocess(tree):
        for key, value in tree.items():
            if condition(key):
                tree[key] = transform(value)

    # ...should be replaced by this one

    from configtree import PostProcessor, Pipeline


    class MyPostProcessor(PostProcessor):

        @Pipeline.worker(100)
        def apply_transform(self, tree, key, value):
            if condition(key):
                tree[key] = transform(value)


    postprocess = MyPostProcessor()


Module :mod:`configtree.conv` and its plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Module :mod:`configtree.conv` is deprecated in favor of :mod:`configtree.formatter`.
The latter one is used by new ``ctdump`` script.  See :ref:`migration03to04-shell-commands` section.

Plugins that use ``configtree.conv`` entry point are deprecated, consider ``configtree.formatter``
entry point.
