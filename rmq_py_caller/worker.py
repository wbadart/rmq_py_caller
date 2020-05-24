import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor


def worker(inputs, ctx, adapter):
    """
    Enter `ctx` and call the resulting function on each message on the queue
    `inputs`.
    """

    async def _main():
        outbox = asyncio.Queue()
        asyncio.create_task(_printer(outbox))
        loop = asyncio.get_running_loop()
        with ctx as func, ThreadPoolExecutor() as pool:
            while True:
                payload = await loop.run_in_executor(pool, inputs.get)
                if payload is None:
                    break
                args = adapter.input(text=payload).first()
                res = func(*args)
                await outbox.put(res)

    async def _printer(inbox):
        while True:
            res = await inbox.get()
            if asyncio.iscoroutine(res):
                res = await res
            json.dump(res, fp=sys.stdout)
            print()

    asyncio.run(_main())
