import asyncio

import httpx2

from simplecron import base
from simplecron.base import Job, logger
from simplecron.context import Context


async def get_api(job: Job, context: Context | None = None, **kwargs):
    async with httpx2.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/todos/1")
        logger.info(f"API response: {response.text}")


base.every(30).seconds.do(get_api)


async def main():
    base.start_blocking()


if __name__ == "__main__":
    asyncio.run(main())
