:mod:`configtree.loader`
------------------------

..  automodule:: configtree.loader

..  autoclass:: Loader

    ..  automethod:: fromconf
    ..  automethod:: __call__

Utilities
~~~~~~~~~

..  autoclass:: Pipeline

    ..  automethod:: worker


Walker
~~~~~~

..  autoclass:: Walker

    ..  automethod:: __call__
    ..  automethod:: walk
    ..  automethod:: ignored
    ..  automethod:: final
    ..  automethod:: environment
    ..  automethod:: regular

..  autoclass:: File

Updater
~~~~~~~

..  autoclass:: Updater

    ..  automethod:: __call__
    ..  automethod:: set_default
    ..  automethod:: call_method
    ..  automethod:: format_value
    ..  automethod:: printf_value
    ..  automethod:: eval_value
    ..  automethod:: required_value

..  autoclass:: UpdateAction

    ..  automethod:: __call__
    ..  automethod:: promise
    ..  automethod:: default_update

..  autoclass:: Promise

    ..  automethod:: __call__

..  autofunction:: resolve
..  autoclass:: ResolverProxy
..  autoclass:: Required

Post processor
~~~~~~~~~~~~~~

..  autoclass:: PostProcessor

    ..  automethod:: __call__
    ..  automethod:: resolve_promise
    ..  automethod:: check_required

..  autoclass:: ProcessingError

Deprecated features
~~~~~~~~~~~~~~~~~~~

..  autofunction:: load
..  autofunction:: loaderconf
..  autofunction:: make_walk
..  autofunction:: make_update
