Changes
=======

0.5.1
-----

*   Fixed bugs in ``Loader`` class.


0.5
---

*   Added abstract base class ``ITree`` to unify type checking;
*   Fixed ``pop`` method of ``Tree`` and ``BranchProxy``;
*   Added ``rare_copy`` method into ``Tree`` and ``BranchProxy``;
*   Unified ``rarefy`` function, it now handles any mapping object.


0.4
---

*   Dropped Python 2.6 support.
*   Completely reworked loading process (see `migration guide`_):

    *   functions ``load``, ``loaderconf`` are deprecated in favor of class ``Loader``;
    *   function ``make_walk`` is deprecated in favor of ``Walker``;
    *   function ``make_update`` is deprecated in favor of ``Updater``;
    *   module ``configtree.conv`` and its plugins (from entry point with
        the same name) is deprecated in favor or ``configtree.formatter``;
    *   shell command ``configtree`` is deprecated in favor of ``ctdump``.


.. _migration guide: http://configtree.readthedocs.org/en/latest/migration.html
                     #migration-from-version-0-3-to-0-4


0.3
---

*   Dropped Python 3.2 support due to ``coverage`` package.  The code should
    still work OK, but it will not be tested anymore.
*   Added ``loaderconf`` function to be able to read loader configuration
    from ``loaderconf.py`` module in a clean way.


0.2
---

*   Added ``copy`` method into ``Tree`` and ``BranchProxy`` classes.
*   Added human readable representation of ``BranchProxy`` class.
*   Added rare iterators into ``Tree`` and ``BranchProxy`` classes.
*   Added ``rarefy`` function.
*   Added rare JSON converter.


0.1
---

*   Initial release.
