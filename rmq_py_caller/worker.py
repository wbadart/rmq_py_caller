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
