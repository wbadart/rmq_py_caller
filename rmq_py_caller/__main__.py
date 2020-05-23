"""rmq_pyctx_caller/__main__.py

Load a context manager and repeatedly call the callable its `__enter__` method
returns.

created: MAY 2020
"""

import json
import sys
from contextlib import nullcontext
from importlib import import_module
from os import environ
from threading import Thread

import jq


def is_context_manager(ctx):
    """Return true if `ctx` has both `__enter__` and `__exit__` attributes."""
    return hasattr(ctx, "__enter__") and hasattr(ctx, "__exit__")


def print_results(func, args, orig):
    """Call `func(**args)` and print the resulting JSON."""
    res = func(*args)
    json.dump({"result": res, "orig": orig}, fp=sys.stdout)
    print()

def main():
    """Setup PY_TARGET and call it on each line of JSON on stdin."""
    exec(environ.get("PY_SETUP", ""), globals())
    ctx = eval(environ["PY_TARGET"])
    if not is_context_manager(ctx):
        ctx = nullcontext(ctx)
    with ctx as func:
        adapter = jq.compile(environ.get("ARG_ADAPTER", "[.]"))
        for payload in sys.stdin:
            obj = json.loads(payload)
            args = adapter.input(obj).first()
            Thread(target=print_results, args=(func, args, obj)).start()


if __name__ == "__main__":
    main()
