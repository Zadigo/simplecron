import asyncio
import json
from collections.abc import Sequence

import httpx2
import redis

from simplecron import base
from simplecron.context import Context
from simplecron.utils import EventListenerEnum, logger

_responses: asyncio.Queue[dict] = asyncio.Queue()

_active_tasks: dict[str, asyncio.Task] = {}


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


def _save_response_done(task: asyncio.Task):
    if task.cancelled():
        logger.warning("Save response task was cancelled")
        return

    if (e := task.exception()) is not None:
        logger.error(f"Save response task failed with exception: {e}")
        return

    logger.info("Save response task completed")


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


async def request(url: str) -> dict:
    async with httpx2.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Request to {data['page']} succeeded")
        return data


async def fetch_data(job: base.Job, **kwargs):
    stop_event: asyncio.Event | None = job.get_base_context.get_value("stop_event")
    url: str = job.get_base_context.get_value("url")

    data = await request(url)

    next_page = job.get_base_context.get_value("next_page")
    total_pages = job.get_base_context.get_value("total_pages")
    logger.info(f"Current page: {next_page}, Total pages: {total_pages}")

    if stop_event is not None and next_page <= 0:
        stop_event.clear()
    else:
        await _responses.put(data)
        logger.info(f"Successfully saved response for page {data['page']} page")


async def scheduler_loop(total_pages: int):
    def decrement_next_page(job: base.Job | Sequence[base.Job]):
        if not isinstance(job, list):
            context = job.get_base_context.decrement_value("next_page")

            next_page = context.json_data.get("next_page")
            url = f"https://recherche-entreprises.api.gouv.fr/search?q=carrefour&page={next_page}"
            context.set_value("url", url)

            logger.info("Next page decremented")

    base.default_scheduler.with_event_listener(
        EventListenerEnum.AFTER, decrement_next_page
    )

    url = "https://recherche-entreprises.api.gouv.fr/search?q=carrefour&page=1"
    base.default_scheduler.with_context(Context(json_data={"url": url}))
    base.every(10).seconds.do(fetch_data)

    await base.async_start_blocking(
        context={"next_page": total_pages, "total_pages": total_pages}
    )


async def main():
    logger.info("Starting main function")

    global_event: asyncio.Event = asyncio.Event()

    url = "https://recherche-entreprises.api.gouv.fr/search?q=carrefour&page=1"
    data = await request(url)

    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(save_response(global_event))
        t2 = tg.create_task(scheduler_loop(data["total_pages"]))

        t1.add_done_callback(_save_response_done)
        t2.add_done_callback(_save_response_done)

        global_event.set()

        _active_tasks["save_response"] = t1
        _active_tasks["scheduler_loop"] = t2


if __name__ == "__main__":
    asyncio.run(main())
