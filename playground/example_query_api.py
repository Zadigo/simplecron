import asyncio

import httpx2

from simplecron import base
from simplecron.base import Job, logger


async def get_api(job: Job):
    async with httpx2.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/todos/1")
        logger.info(f"API response: {response.status_code}")


base.every(30).seconds.do(get_api)


async def main():
    await base.async_start_blocking()


if __name__ == "__main__":
    asyncio.run(main())
