"""Collect your 1st-degree connections from the My Network page."""
import csv
import random
import re

from . import config
from .browser import open_browser, check_blocked
from .util import profile_url

PAGE = "https://www.linkedin.com/mynetwork/invite-connect/connections/"


async def _harvest(page, found):
    links = page.locator('main a[href*="/in/"]')
    for i in range(await links.count()):
        a = links.nth(i)
        try:
            url = profile_url(await a.get_attribute("href"))
            if not url or url in found:
                continue
            text = [t.strip() for t in (await a.inner_text(timeout=1000)).split("\n") if t.strip()]
            if not text:          # photo link - the text link carries the name
                continue
            found[url] = {"name": text[0], "headline": text[1] if len(text) > 1 else "", "url": url}
        except Exception:
            continue


async def collect(limit=None):
    found = {}
    async with open_browser() as page:
        await page.goto(PAGE, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        check_blocked(page)
        stale = 0
        while stale < 4:
            before = len(found)
            await _harvest(page, found)
            print(f"  {len(found)} connections so far")
            if limit and len(found) >= limit:
                break
            more = page.locator("main button", has_text=re.compile(r"(show|load|see) more", re.I))
            if await more.count():
                try:
                    await more.first.scroll_into_view_if_needed(timeout=3000)
                    await more.first.click(timeout=3000)
                except Exception:
                    pass
            links = page.locator('main a[href*="/in/"]')
            if await links.count():
                try:
                    await links.last.scroll_into_view_if_needed(timeout=3000)
                except Exception:
                    pass
            await page.keyboard.press("End")
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(random.randint(2000, 3500))
            stale = stale + 1 if len(found) == before else 0

    rows = list(found.values())
    rows = rows[:limit] if limit else rows
    config.URLS.write_text("\n".join(r["url"] for r in rows) + "\n", encoding="utf-8")
    with config.CONNECTIONS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "headline", "url"])
        w.writeheader(); w.writerows(rows)
    print(f"\n✓ {len(rows)} connections saved to {config.URLS.name} and {config.CONNECTIONS_CSV.name}")
