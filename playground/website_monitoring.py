import asyncio

from playwright.async_api import Page, async_playwright

from simplecron import base
from simplecron.base import Job, logger
from simplecron.context import Context

page_lock = asyncio.Lock()


async def monitor_page(job: Job, context: Context | None = None, **kwargs):
    async with page_lock:
        if context is not None:
            page: Page = context.json_data.get("page")
            print(context)
            if page is not None:
                print(page)
                await page.reload()
            logger.info("Page monitored...")


async def main():
    async with async_playwright() as p:
        base.every(10).seconds.do(monitor_page)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto("https://example.com")
        await base.async_start_blocking(context={"page": page})

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
