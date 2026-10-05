import asyncio
import contextlib
import json
from collections.abc import Sequence

import httpx2
import redis

from simplecron import base
from simplecron.utils import EventListenerEnum, logger

PAGE: int = 1

_responses: asyncio.Queue[dict] = asyncio.Queue()

_active_tasks: dict[str, asyncio.Task] = {}


def next_page_event_listener(job: Sequence[base.Job]):
    global PAGE
    PAGE += 1


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

        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(cancel.wait(), timeout=1)


async def request(url: str) -> dict:
    async with httpx2.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Request to {data['page']} succeeded")
        return data


async def fetch_data(job: base.Job, context: base.Context | None = None, **kwargs):
    stop_event: asyncio.Event | None = context.json_data.get("stop_event")
    url: str = kwargs.get("url")

    data = await request(url)
    if stop_event is not None:
        total_pages = context.json_data.get("total_pages")
        current_page = data.get("page")

        logger.info(f"Current page: {current_page}, Total pages: {total_pages}")
        if current_page >= total_pages:
            stop_event.clear()

    await _responses.put(data)
    logger.info(f"Successfully saved response for page {data['page']} page")


async def main():
    logger.info("Starting main function")

    global_event: asyncio.Event = asyncio.Event()

    url = f"https://recherche-entreprises.api.gouv.fr/search?q=carrefour&page={PAGE}"

    data = await request(url)
    total_pages = data["total_pages"]

    global_event.set()
    task = asyncio.create_task(save_response(global_event))
    task.add_done_callback(_save_response_done)
    _active_tasks["save_response"] = task

    base.default_scheduler.with_event_listener(
        EventListenerEnum.AFTER, next_page_event_listener
    )
    base.every(10).seconds.do(fetch_data, url=url)

    await base.async_start_blocking(context={"total_pages": total_pages})


if __name__ == "__main__":
    asyncio.run(main())
