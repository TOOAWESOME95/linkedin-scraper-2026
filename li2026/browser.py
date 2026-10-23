"""Browser + session handling (Playwright storage-state JSON)."""
import json
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright

from . import config

BLOCK_MARKERS = ("checkpoint", "authwall", "/login", "/uas/login")


class Blocked(RuntimeError):
    """LinkedIn showed a login wall, security checkpoint or CAPTCHA."""


@asynccontextmanager
async def open_browser(need_session=True, headless=None):
    if need_session and not config.SESSION.exists():
        raise SystemExit(f"No session found at {config.SESSION}\nRun:  py li.py login")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=config.HEADLESS if headless is None else headless)
        opts = {"viewport": config.VIEWPORT}
        if need_session:
            opts["storage_state"] = str(config.SESSION)
        context = await browser.new_context(**opts)
        page = await context.new_page()
        try:
            yield page
        finally:
            await context.close()
            await browser.close()


def check_blocked(page):
    if any(m in page.url for m in BLOCK_MARKERS):
        raise Blocked(f"LinkedIn security check / logged out at {page.url}. "
                      "Clear it in your normal browser and wait a day before running again.")


async def is_logged_in(page):
    if any(m in page.url for m in BLOCK_MARKERS):
        return False
    return "/feed" in page.url or await page.locator('a[href*="/mynetwork/"]').count() > 0


async def login(timeout_s=300):
    """Open a browser, let the user log in by hand (2FA etc.), save the session."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(viewport=config.VIEWPORT)
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")
        print("Log in to LinkedIn in the browser window (including any 2FA).")
        print(f"Waiting up to {timeout_s // 60} minutes...")
        for _ in range(timeout_s):
            await page.wait_for_timeout(1000)
            if await is_logged_in(page):
                break
        else:
            await browser.close()
            raise SystemExit("Timed out waiting for login.")
        await page.wait_for_timeout(3000)
        state = await context.storage_state()
        config.SESSION.write_text(json.dumps(state, indent=2), encoding="utf-8")
        await browser.close()
    print(f"✓ Session saved to {config.SESSION}")
