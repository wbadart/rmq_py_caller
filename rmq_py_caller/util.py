"""rmq_py_caller/util.py

Miscellaneous, private utilities for running rmq_py_caller.
created: MAY 2020
"""

from contextlib import contextmanager


def is_context_manager(ctx):
    """Return true if `ctx` has both `__enter__` and `__exit__` attributes."""
    return hasattr(ctx, "__enter__") and hasattr(ctx, "__exit__")


@contextmanager
def joining(obj):
    """Call `obj.join` when the context exits."""
    try:
        yield obj
    finally:
        obj.join()
