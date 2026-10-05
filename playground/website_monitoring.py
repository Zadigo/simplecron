import asyncio

from playwright.async_api import Page, async_playwright

from simplecron import base
from simplecron.base import Job, logger

page_lock = asyncio.Lock()


async def monitor_page(job: Job, **kwargs):
    async with page_lock:
        page: Page = job.get_base_context.get_value("page")
        if page is not None:
            title_handle = await page.query_selector("title")
            if title_handle is not None:
                title = await title_handle.text_content()
                logger.info(f"Page title: {title}")


async def main():
    async with async_playwright() as p:
        job = base.every(10).seconds.do(monitor_page)
        job.with_limited_runs(3)

        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto("https://example.com")
        await base.async_start_blocking(context={"page": page})

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
