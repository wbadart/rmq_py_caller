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
from threading import Thread

import jq


def is_context_manager(ctx):
    """Return true if `ctx` has both `__enter__` and `__exit__` attributes."""
    return hasattr(ctx, "__enter__") and hasattr(ctx, "__exit__")


def apply_func(func, args, orig):
    """Call `func(**args)` and print the resulting JSON."""
    res = func(*args)
    json.dump({"result": res, "orig": orig}, fp=sys.stdout)
    print()


async def main():
    """Setup PY_TARGET and call it on each line of JSON on stdin."""
    exec(environ.get("PY_SETUP", ""), globals())
    ctx = eval(environ["PY_TARGET"])
    if not is_context_manager(ctx):
        ctx = nullcontext(ctx)
    with ctx as func, ThreadPoolExecutor() as background_thread:
        adapter = jq.compile(environ.get("ARG_ADAPTER", "[.]"))
        for payload in sys.stdin:
            obj = json.loads(payload)
            args = adapter.input(obj).first()
            background_thread.submit(apply_func, func, args, obj)


if __name__ == "__main__":
    asyncio.run(main())
