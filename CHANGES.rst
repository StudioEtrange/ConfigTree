Changes
=======

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
