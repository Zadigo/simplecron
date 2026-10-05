import asyncio

from simplecron import base


async def executor(*args, **kwargs):
    print("Executed!")


async def main():
    base.every(5).seconds.do(executor)
    while True:
        base.run_pending()
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
