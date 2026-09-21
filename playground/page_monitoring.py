from playwright.sync_api import Page, sync_playwright

from simplecron import base
from simplecron.base import Job, logger
from simplecron.context import Context


def monitor_page(job: Job, context: Context | None = None, **kwargs):
    page: Page = context.json_data.get("page")
    if page is not None:
        page.reload()
    logger.info("Page monitored...")


base.every(30).seconds.do(monitor_page)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://example.com")
        base.start_blocking(context={"page": page})

        browser.close()


if __name__ == "__main__":
    main()
