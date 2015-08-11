:mod:`configtree.tree`
----------------------

..  automodule:: configtree.tree

..  autoclass:: ITree

..  autoclass:: Tree

    The tree object provides complete :class:`collections.abc.MutableMapping`
    interface.  So that it can be used where built-in :class:`dict`
    is expected.  Additionally, the following methods are available that
    extend class functionality.

    ..  automethod:: branch
    ..  automethod:: rare_keys
    ..  automethod:: rare_values
    ..  automethod:: rare_items
    ..  automethod:: copy

..  autoclass:: BranchProxy

    ..  automethod:: copy
    ..  automethod:: as_tree

..  autofunction:: flatten
..  autofunction:: rarefy
