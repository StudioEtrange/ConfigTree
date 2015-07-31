Migration from version 0.3 to 0.4
=================================

.. _shell-commands:

Shell commands
--------------

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
-----------------

The following functions are deprecated:

*   :func:`configtree.loader.make_walk` in favor of :class:`configtree.loader.Walker`;
*   :func:`configtree.loader.make_update` in favor of :class:`configtree.loader.Updater`;

Simple replacement gives the same result.

Function ``postprocess`` should be created using class :class:`configtree.loader.PostProcessor`.
If there is no built-in features you need, consider extending of the class.


Module :mod:`configtree.conv` and entry point ``configtree.conv``
-----------------------------------------------------------------

Module :mod:`configtree.conv` is deprecated in favor of :mod:`configtree.formatter`.
The latter one is used by new ``ctdump`` script.  See :ref:`shell-commands` section.

Plugins that use this entry point are deprecated, consider ``configtree.formatter``
entry point.
