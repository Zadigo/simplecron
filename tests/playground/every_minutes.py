import asyncio


async def google():
    while True:
        print("Hello, World 1!")
        await asyncio.sleep(1)


async def facebook():
    while True:
        print("Hello, World 2!")
        await asyncio.sleep(3)


async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(google())
        tg.create_task(facebook())

if __name__ == "__main__":
    asyncio.run(main())
