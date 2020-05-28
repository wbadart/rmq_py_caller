"""rmq_py_caller/app.py

Exports `main_loop`, which launches the rmq_py_caller application.
created: MAY 2020
"""

import asyncio
import inspect
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from queue import Queue
from threading import Thread

__all__ = ["main_loop"]


def main_loop(ctx, adapter, fs_in=sys.stdin, fs_out=sys.stdout):
    """Start a `worker` thread and send it inputs from `fs_in`."""
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
            if line:
                payload = json.loads(line)
                worker_inbox.put(payload)
    finally:
        worker_inbox.put(None)  # Tell `worker` to shutdown by sending `None`
        worker_thread.join()
        log.info("Goodbye from rmq_py_caller!")


def worker(inputs, ctx, adapter, fs_out=sys.stdout):
    """Enter `ctx` and call the resulting function on messages from `inputs`."""
    log = logging.getLogger(__name__)

    async def _main():
        # If `func` is a coroutine, we don't want to wait for it here; we want
        # to move on to the next input. We'll send it to `_printer` via
        # `outbox` to await the result for us and print it to `fs_out`.
        outbox = asyncio.Queue()
        printer_task = asyncio.create_task(_printer(outbox))
        loop = asyncio.get_running_loop()

        with ctx as func, ThreadPoolExecutor() as bg_thread:
            while True:
                # `inputs` is a synchronous queue so calling `inputs.get` would
                # block the current thread. Calling it in `bg_thread` allows
                # our thread to stay unblocked
                log.info("Waiting for payload...")
                payload = await loop.run_in_executor(bg_thread, inputs.get)
                log.debug("Got payload: %s", payload)
                if payload is None:
                    break  # Receiving `None` means time to shut down

                args = adapter.input(payload).first()  # call the jq program
                result = func(*args)
                await outbox.put((result, payload))
                log.debug("ARG_ADAPTER resulted in: %s", args)
                log.debug("PY_TARGET resulted in: %s", result)

            printer_task.cancel()
            log.info("Goodbye from rmq_py_caller worker!")

    async def _printer(inbox):
        while True:
            result, orig = await inbox.get()
            if inspect.isawaitable(result):
                log.info("_printer got an awaitable. Awaiting it...")
                result = await result
                log.debug("Done! Got: %s", result)
            json.dump({"result": result, "orig": orig}, fp=fs_out)
            fs_out.write("\n")

    asyncio.run(_main())


def _is_context_manager(ctx):
    return hasattr(ctx, "__enter__") and hasattr(ctx, "__exit__")
