import asyncio

from simplecron.base import default_scheduler


async def some_function():
    print("Executed!")


async def main():
    default_scheduler.(some_function, "interval", seconds=5)
    await default_scheduler.start()


if __name__ == "__main__":
    asyncio.run(main())
