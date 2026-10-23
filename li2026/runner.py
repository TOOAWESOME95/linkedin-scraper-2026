"""Batch jobs: scrape, contacts-only, visit."""
import asyncio
import json
import random

from . import config, memory
from .browser import open_browser, check_blocked, Blocked
from .profile import scrape_profile, contact_info
from .util import read_urls, pause


def _load():
    if config.PROFILES_JSON.exists():
        return json.loads(config.PROFILES_JSON.read_text(encoding="utf-8"))
    return {}


def _save(data):
    config.PROFILES_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


async def scrape(urls_file=None, limit=None, refresh=False, contacts=True):
    limit = limit or config.SCRAPE_MAX_PER_RUN
    urls, data, recent = read_urls(urls_file), _load(), memory.recent()
    skip = recent if refresh else set(data) | recent
    todo = [u for u in urls if u not in skip]
    left = len(todo); todo = todo[:limit]
    print(f"{len(todo)} to scrape this run · {len(urls) - left} already done/recent · "
          f"{left - len(todo)} left for later runs (cap {limit})")
    if not todo:
        return
    async with open_browser() as page:
        for i, url in enumerate(todo, 1):
            try:
                p = await scrape_profile(page, url, with_contact=contacts, debug_dir=config.DEBUG_DIR)
                data[url] = p; _save(data); memory.log(url, "scrape")
                print(f"✓ {i}/{len(todo)} {p['name']} | {p['headline']} | {p['location'] or '-'} "
                      f"| exp {len(p['experience_raw'])} | edu {len(p['education_raw'])} "
                      f"| {p['email'] or 'no email'}")
            except Blocked as e:
                memory.log(url, "scrape", "blocked"); print("✗", e); break
            except Exception as e:
                memory.log(url, "scrape", "error"); print(f"✗ {url}: {e}")
            if i < len(todo):
                await asyncio.sleep(pause(config.SCRAPE_DELAY))
    print(f"\nSaved to {config.PROFILES_JSON}  ·  run  py li.py export  for a CSV")


async def contacts_only(urls_file=None, limit=None):
    limit = limit or config.SCRAPE_MAX_PER_RUN
    data = _load()
    todo = [u for u in read_urls(urls_file) if u in data and "email" not in data[u]][:limit]
    print(f"{len(todo)} already-scraped people need contact info")
    if not todo:
        return
    async with open_browser() as page:
        for i, url in enumerate(todo, 1):
            try:
                c = await contact_info(page, url)
            except Blocked as e:
                print("✗", e); break
            data[url].update(c); _save(data); memory.log(url, "contact")
            print(f"✓ {i}/{len(todo)} {data[url].get('name')}: {c['email'] or '(no email shared)'}")
            if i < len(todo):
                await asyncio.sleep(pause(config.SCRAPE_DELAY))


async def visit(urls_file=None, limit=None):
    limit = limit or config.VISIT_MAX_PER_RUN
    urls, recent = read_urls(urls_file), memory.recent()
    todo = [u for u in urls if u not in recent][:limit]
    random.shuffle(todo)
    print(f"{len(todo)} to visit ({len(urls) - len(todo)} skipped: visited recently or over cap)")
    if not todo:
        return
    async with open_browser() as page:
        for i, url in enumerate(todo, 1):
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(random.randint(3000, 5000))
            try:
                check_blocked(page)
            except Blocked as e:
                memory.log(url, "visit", "blocked"); print("✗", e); break
            for _ in range(random.randint(2, 4)):
                await page.mouse.wheel(0, random.randint(300, 700))
                await page.wait_for_timeout(random.randint(1200, 3000))
            await page.mouse.wheel(0, -1500)
            await page.wait_for_timeout(random.randint(1000, 2500))
            memory.log(url, "visit")
            print(f"✓ {i}/{len(todo)} {(await page.title()).replace(' | LinkedIn', '')}")
            if i < len(todo):
                await asyncio.sleep(pause(config.VISIT_DELAY))
