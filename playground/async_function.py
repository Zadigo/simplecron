import asyncio

from simplecron import base


async def some_function(*args, **kwargs):
    print("Executed!")


async def main():
    base.every(5).seconds.do(some_function)
    while True:
        base.run_pending()
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
