"""rmq_pyctx_caller/__main__.py

Load a context manager and repeatedly call the callable its `__enter__` method
returns.

created: MAY 2020
"""

import json
import sys
from contextlib import nullcontext
from os import environ
from queue import Queue
from threading import Thread

import jq

from rmq_py_caller.util import is_context_manager, joining


def print_results(func, queue):
    """Call `func(**args)` and print the resulting JSON."""
    while True:
        args, orig = queue.get()
        res = func(*args)
        json.dump({"result": res, "orig": orig}, fp=sys.stdout)
        print()
        queue.task_done()


def main():
    """Setup PY_TARGET and call it on each line of JSON on stdin."""
    exec(environ.get("PY_SETUP", ""), globals())
    ctx = eval(environ["PY_TARGET"])
    if not is_context_manager(ctx):
        ctx = nullcontext(ctx)
    with ctx as func, joining(Queue()) as queue:
        adapter = jq.compile(environ.get("ARG_ADAPTER", "[.]"))
        Thread(target=print_results, args=(func, queue), daemon=True).start()
        for payload in sys.stdin:
            obj = json.loads(payload)
            args = adapter.input(obj).first()
            queue.put((args, obj))


if __name__ == "__main__":
    main()
