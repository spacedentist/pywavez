import asyncio
import inspect
import logging
import re


async def waitForOne(*aws, timeout=None):
    _, pending = await asyncio.wait(
        aws, timeout=timeout, return_when=asyncio.FIRST_COMPLETED
    )
    for f in pending:
        f.cancel()


__rex_to_camel_case = re.compile(r"_.")


def toCamelCase(x):
    return __rex_to_camel_case.sub(
        lambda m: m.group(0)[1].upper(), x.strip("_").lower()
    )


def callSoon(func, *args, **kwargs):
    async def makeCall():
        ret = func(*args, **kwargs)
        if inspect.isawaitable(ret):
            await ret

    asyncio.get_event_loop().call_soon(lambda: spawnTask(makeCall()))


def spawnTask(coro):
    task = asyncio.create_task(coro)
    task.add_done_callback(logException)
    return task


def logException(task):
    if not task.cancelled():
        ex = task.exception()
        if ex is not None and type(ex) is not KeyboardInterrupt:
            logging.error(repr(ex))
            task.print_stack()
