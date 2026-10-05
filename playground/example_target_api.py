import asyncio
import json
from typing import Any

import httpx2
import redis

from simplecron import base
from simplecron.utils import logger

_responses: asyncio.Queue[dict | Any] = asyncio.Queue()

_active_tasks: dict[str, asyncio.Task] = {}

_request_tasks: set[asyncio.Task] = set()


def get_redis() -> redis.Redis:
    logger.info("Connecting to Redis instance")
    instance = redis.Redis()
    try:
        instance.ping()
        logger.info("Successfully connected to Redis")
    except redis.ConnectionError:
        logger.error("Failed to connect to Redis")
        raise redis.ConnectionError("Failed to connect to Redis")
    return instance


async def request(page: int = 1) -> dict:
    async with asyncio.Semaphore(8), httpx2.AsyncClient() as client:
        url = (
            f"https://recherche-entreprises.api.gouv.fr/search?q=carrefour&page={page}"
        )
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

        await _responses.put(data)

        logger.info(f"Request to {data['page']} succeeded")
        return data


def _done_callback(task: asyncio.Task):
    if task.cancelled():
        logger.warning(f"{task.get_name()} response task was cancelled")
        return

    if (e := task.exception()) is not None:
        logger.error(f"{task.get_name()} task failed with exception: {e}")
        return

    _request_tasks.discard(task)
    logger.info(f"{task.get_name()} task completed")


async def save_response(cancel: asyncio.Event):
    await cancel.wait()
    logger.info("Starting save_response task")

    db = get_redis()

    while cancel.is_set():
        while not _responses.empty():
            data = await _responses.get()
            db.lpush("simplecron-responses", json.dumps(data))
        await asyncio.sleep(3)

        # with contextlib.suppress(asyncio.TimeoutError):
        #     await asyncio.wait_for(cancel.wait(), timeout=1)


async def fetch_data(job: base.Job, **kwargs):
    async with asyncio.TaskGroup() as tg:
        for _ in range(10):
            job.get_base_context.decrement_value("current_page")

            page = job.get_base_context.get_value("current_page")
            if page == 0:
                stop_event: asyncio.Event = job.get_base_context.get_value("stop_event")
                if stop_event is not None:
                    for task in _active_tasks.values():
                        task.cancel("Global loop reached")
                    stop_event.clear()

            task = tg.create_task(request(page), name="Request")

            _request_tasks.add(task)

            task.add_done_callback(_done_callback)
            await asyncio.sleep(3)


async def scheduler_loop(total_pages: int):
    base.every(60).seconds.do(fetch_data)

    await base.async_start_blocking(
        context={"current_page": total_pages, "total_pages": total_pages}
    )


async def main():
    logger.info("Starting main function")

    global_event: asyncio.Event = asyncio.Event()

    data = await request()

    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(save_response(global_event), name="SaveResponse")
        t2 = tg.create_task(scheduler_loop(data["total_pages"]), name="SchedulerLoop")

        global_event.set()

        t1.add_done_callback(_done_callback)
        t2.add_done_callback(_done_callback)

        _active_tasks["save_response"] = t1
        _active_tasks["scheduler_loop"] = t2


if __name__ == "__main__":
    asyncio.run(main())
