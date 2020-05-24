"""rmq_pyctx_caller/__main__.py

Load a context manager and repeatedly call the callable its `__enter__` method
returns.

created: MAY 2020
"""

import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from os import environ
from queue import Queue
from threading import Thread

import jq

from rmq_py_caller.worker import worker


def is_context_manager(ctx):
    """Return true if `ctx` has both `__enter__` and `__exit__` attributes."""
    return hasattr(ctx, "__enter__") and hasattr(ctx, "__exit__")


def main():
    """Setup PY_TARGET and call it on each line of JSON on stdin."""
    exec(environ.get("PY_SETUP", ""), globals())
    ctx = eval(environ["PY_TARGET"])
    if not is_context_manager(ctx):
        ctx = nullcontext(ctx)

    adapter = jq.compile(environ.get("ARG_ADAPTER", "[.]"))
    queue = Queue()
    Thread(target=worker, args=(queue, ctx, adapter), daemon=True).start()

    for line in sys.stdin:
        queue.put(line)
    queue.put(None)


if __name__ == "__main__":
    main()
