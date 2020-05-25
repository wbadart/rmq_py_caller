"""rmq_pyctx_caller/__main__.py

Load a context manager and call the callable its `__enter__` method returns on
lines of JSON from stdin.

created: MAY 2020
"""

import json
import logging
import sys
from argparse import ArgumentParser
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
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="-v to include info, -vv to include debugging",
    )
    args = parser.parse_args()

    # If you're curious about the use exec/ eval here, please see the project
    # wiki for discussion.
    # pylint: disable=exec-used,eval-used
    exec(environ.get("PY_SETUP", ""), globals())
    ctx = eval(environ["PY_TARGET"])
    # Wait until now to call basicConfig in case PY_SETUP wants to do it
    if args.verbose:
        logging.basicConfig(
            level=[logging.WARN, logging.INFO, logging.DEBUG][args.verbose]
        )
    log = logging.getLogger(__name__)
    log.debug("Got PY_TARGET: %s", ctx)

    # Our worker will use ctx in a `with` statement shortly (for resource
    # management). If PY_TARGET is just a regular function, wrap it in the
    # nullcontext so we can pretend it's a context manager that yields the
    # function (and in so doing, not have to invent specialized handling; keep
    # it to one unified process).
    if not is_context_manager(ctx):
        ctx = nullcontext(ctx)

    # `worker` will run in a different thread so that it can keep at it while
    # we're blocked reading stdin. We'll send it inputs via a thread-safe
    # stdlib queue.Queue.
    adapter = jq.compile(environ.get("ARG_ADAPTER", "[.]"))
    log.debug("Using ARG_ADAPTER: %s", adapter.program_string)
    queue = Queue()
    worker_args = queue, ctx, adapter
    worker_thread = Thread(target=worker, args=worker_args)
    worker_thread.start()

    for line in sys.stdin:
        log.debug("Read stdin line: %s", line)
        payload = json.loads(line)
        queue.put(payload)
    # When there's no more input, tell `worker` to shutdown by sending `None`
    queue.put(None)
    worker_thread.join()
    log.info("Goodbye from rmq_py_caller!")


if __name__ == "__main__":
    main()
