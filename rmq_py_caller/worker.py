"""rmq_py_caller/worker.py

This module exports the `worker` function. Calling `worker` will spin up an
async program that will process JSON objects you send to its `inputs` queue.

created: MAY 2020
"""

import asyncio
import inspect
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor

__all__ = ["worker"]


def worker(inputs, ctx, adapter, fs_out=sys.stdout):
    """
    Enter `ctx` and call the resulting function on each message on the queue
    `inputs`.
    """
    log = logging.getLogger(__name__)

    async def _main():
        # _main is responsible for calling func. However, sometimes func might
        # be a coroutine, and _main doesn't wan't to `await` the result before
        # moving onto the next queue item. Instead, send results (via the
        # `outbox` queue) to the _printer task, which will `await` and print
        # the reult.
        outbox = asyncio.Queue()
        printer_task = asyncio.create_task(_printer(outbox))

        # Need a handle on the event loop for run_in_executor; see below
        loop = asyncio.get_running_loop()

        # Enter ctx to perform any setup for func, and guarantee teardown
        with ctx as func, ThreadPoolExecutor() as bg_thread:
            while True:
                # `inputs` is a synchronous queue (stdlib queue.Queue) so .get
                # would block the current thread. Running in a separate
                # executor (bg_thread) allows this thread to stay unblocked, in
                # turn allowing the loop to schedule other tasks while we await
                # a payload
                log.info("Waiting for payload...")
                payload = await loop.run_in_executor(bg_thread, inputs.get)
                log.debug("Got payload: %s", payload)

                # rmq_py_caller.__main__.main will send us `None` when it's
                # time to shutdown
                if payload is None:
                    break

                # Apply ARG_ADAPTER (which maps the input object to an array of
                # args for PY_TARGET), call PY_TARGET, and send the result to
                # the _printer
                args = adapter.input(payload).first()
                log.debug("ARG_ADAPTER resulted in: %s", args)
                result = func(*args)
                log.debug("PY_TARGET resulted in: %s", result)
                await outbox.put((result, payload))

            printer_task.cancel()
            log.info("Goodbye from rmq_py_caller worker!")

    async def _printer(inbox):
        # I just wait for _main to send me stuff to print. If what _main sends
        # me is a coroutine object, I'll wait on that too before printing.
        while True:
            result, orig = await inbox.get()
            if inspect.isawaitable(result):
                log.info("_printer got an awaitable. Awaiting it...")
                result = await result
                log.debug("Done!")
            json.dump({"result": result, "orig": orig}, fp=fs_out)
            fs_out.write("\n")

    asyncio.run(_main())
