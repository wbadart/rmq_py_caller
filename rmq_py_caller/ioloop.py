"""rmq_py_caller/ioloop.py

This is the "main loop" of rmq_py_caller which interacts with the blocking
world of IO.

created: MAY 2020
"""

import json
import logging
import sys
from contextlib import nullcontext
from queue import Queue
from threading import Thread

from rmq_py_caller.worker import worker

__all__ = ["main_loop"]


def main_loop(ctx, adapter, fs_in=sys.stdin, fs_out=sys.stdout):
    """
    Start a worker thread and send it inputs from `fs_in`. The worker will
    enter `ctx` if it is a context manager and call the function its __enter__
    method returns on the inputs we send from `fs_in`.
    """
    log = logging.getLogger(__name__)

    # If PY_TARGET is a regular function, wrap it in nullcontext so we can
    # pretend it's a context manager (`worker` uses it in a `with` statement)
    if not _is_context_manager(ctx):
        ctx = nullcontext(ctx)

    # `worker` gets its own thread so it can run while we're blocked reading `fs_in`
    worker_inbox = Queue()
    worker_thread = Thread(target=worker, args=(worker_inbox, ctx, adapter, fs_out))
    worker_thread.start()
    try:
        for line in fs_in:
            log.debug("Read %s line: %s", fs_in, line)
            payload = json.loads(line)
            worker_inbox.put(payload)
    finally:
        # When there's no more input, tell `worker` to shutdown by sending `None`
        worker_inbox.put(None)
        worker_thread.join()
        log.info("Goodbye from rmq_py_caller!")


def _is_context_manager(ctx):
    return hasattr(ctx, "__enter__") and hasattr(ctx, "__exit__")
