"""rmq_pyctx_caller/__main__.py

Load a context manager and repeatedly call the callable its `__enter__` method
returns.

created: MAY 2020
"""

import importlib
import json
import sys
from os import environ

import jq


def main():
    """Setup the context manager at `CTX_MODULE.CTX_NAME` and call the callable
    it yields for each line of stdin.
    """
    module = importlib.import_module(environ["CTX_MODULE"])
    ctx = getattr(module, environ["CTX_NAME"])
    adapter = jq.compile(environ["ARG_ADAPTER"])
    with ctx as func:
        for payload in sys.stdin:
            obj = json.loads(payload)
            args = adapter.input(obj).first()
            res = func(**args)
            json.dump({"result": res, "orig": obj}, fp=sys.stdout)
            print()


if __name__ == "__main__":
    main()
