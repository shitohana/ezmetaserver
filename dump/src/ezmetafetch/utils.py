import asyncio
import time

async def run_in_semaphore(sem: asyncio.Semaphore, coro):
    res = await coro
    sem.release()
    return res


async def run_coros_limited(coros: list, rate_limit: int):
    sem = asyncio.Semaphore(rate_limit + 1)
    async with sem:
        tasks = []
        for coro in coros:
            started = time.time()
            await sem.acquire()
            tasks.append(asyncio.create_task(run_in_semaphore(sem, coro)))

            while time.time() - started < 1 / rate_limit:
                await asyncio.sleep(0.1)

        result = await asyncio.gather(*tasks)
    return result
