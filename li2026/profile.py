"""Profile scraping for the 2026 layout.

LinkedIn now ships scrambled CSS classes, so sections are located by their
`componentkey` attributes (e.g. ...Topcard, ...About, profileCards...) and
headings, and only *visible* text is read.
"""
import random
import re
from datetime import datetime

from .browser import check_blocked
from .util import clean


async def card_lines(page, key_fragment):
    loc = page.locator(f'[componentkey*="{key_fragment}"]').first
    if await loc.count() == 0:
        return []
    try:
        return clean((await loc.inner_text(timeout=3000)).split("\n"))
    except Exception:
        return []


def parse_topcard(top, name=None):
    """-> (name, headline, location) from the top-card text lines."""
    name = name or (top[0] if top else None)
    rest = [l for l in top if l != name and not l.startswith("·")]
    headline = rest[0] if rest else None
    location = next((l for l in rest[1:] if l != headline and re.search(r",\s*[A-Z]", l)
                     and len(l) < 80 and "follower" not in l and "connection" not in l
                     and " + " not in l), None)
    return name, headline, location


async def section_by_heading(page, heading):
    h = page.locator("h2", has_text=re.compile(rf"^\s*{heading}\s*$")).first
    if await h.count() == 0:
        return []
    sec = h.locator("xpath=ancestor::section[1]")
    if await sec.count() == 0:
        sec = h.locator("xpath=ancestor::*[4]")
    try:
        lines = clean((await sec.first.inner_text(timeout=3000)).split("\n"))
    except Exception:
        return []
    return [l for l in lines if l != heading]


async def load_lazy_sections(page):
    """Scroll each lazy profile card into view and wait for it to render."""
    for _ in range(6):
        await page.mouse.wheel(0, 900)
        await page.wait_for_timeout(random.randint(700, 1300))
    lazy = page.locator('[componentkey^="profileCards"]')
    for i in range(await lazy.count()):
        el = lazy.nth(i)
        try:
            await el.scroll_into_view_if_needed(timeout=3000)
            for _ in range(16):
                if len((await el.inner_text(timeout=1000)).strip()) > 20:
                    break
                await page.wait_for_timeout(500)
        except Exception:
            pass


STOPS = ("More profiles for you", "People you may know", "Explore Premium profiles",
         "You might like", "LinkedIn Corporation", "Accessibility")
DROP = {"Experience", "Education", "Skills", "Back", "All", "Industry Knowledge",
        "Tools & Technologies", "Interpersonal Skills", "Other Skills", "Present"}


def parse_details_text(lines):
    out = []
    for l in clean(lines):
        if l.startswith(STOPS):
            break
        if l in DROP or l.startswith(("Nothing to see", "Skills that ", "Experience that ",
                                      "Education that ")):
            continue
        out.append(l)
    return out


async def details_page(page, base, slug):
    await page.goto(base.rstrip("/") + f"/details/{slug}/", wait_until="domcontentloaded")
    await page.wait_for_timeout(4000)
    check_blocked(page)
    for _ in range(5):
        await page.mouse.wheel(0, 1200)
        await page.wait_for_timeout(800)
    main = page.locator("main").first
    if await main.count() == 0:
        return []
    return parse_details_text((await main.inner_text(timeout=5000)).split("\n"))


def parse_contact(text, hrefs):
    emails = {h[7:].split("?")[0] for h in hrefs if h.lower().startswith("mailto:")}
    emails |= set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text))
    phone = ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if l.lower() == "phone" and i + 1 < len(lines):
            phone = re.sub(r"\s*\((mobile|work|home)\)", "", lines[i + 1], flags=re.I)
            break
    sites = sorted({h for h in hrefs if h.startswith("http") and "linkedin.com" not in h})
    return {"email": "; ".join(sorted(emails)), "phone": phone, "websites": sites}


async def contact_info(page, base):
    """Email / phone / websites - only what the person shares with connections."""
    try:
        await page.goto(base.rstrip("/") + "/overlay/contact-info/", wait_until="domcontentloaded")
        await page.wait_for_timeout(random.randint(3000, 4500))
        check_blocked(page)
        box = page.locator('[role="dialog"]').first
        if await box.count() == 0:
            box = page.locator("main").first
        text = await box.inner_text(timeout=5000)
        hrefs = await box.locator("a[href]").evaluate_all("els => els.map(e => e.href)")
    except Exception as e:
        if e.__class__.__name__ == "Blocked":
            raise
        return {"email": "", "phone": "", "websites": []}
    return parse_contact(text, hrefs)


async def scrape_profile(page, url, with_contact=True, debug_dir=None):
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(4000)
    check_blocked(page)

    top = await card_lines(page, "Topcard")
    h2 = page.locator('[componentkey*="Topcard"] h2').first
    name = (await h2.inner_text()).strip() if await h2.count() else None
    name, headline, location = parse_topcard(top, name)

    about = [l for l in await card_lines(page, "About") if l != "About"]
    about = " ".join(about) or None

    await load_lazy_sections(page)
    experience = await section_by_heading(page, "Experience")
    education = await section_by_heading(page, "Education")
    skills = await section_by_heading(page, "Skills")

    if not experience and debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        (debug_dir / f"{slug}.html").write_text(await page.content(), encoding="utf-8")

    contact = await contact_info(page, url) if with_contact else {}
    if not experience:
        experience = await details_page(page, url, "experience")
    if not education:
        education = await details_page(page, url, "education")
    if not skills:
        skills = await details_page(page, url, "skills")

    return {
        "url": url, "name": name, "headline": headline, "location": location, "about": about,
        "email": contact.get("email", ""), "phone": contact.get("phone", ""),
        "websites": contact.get("websites", []),
        "experience_raw": [l for l in experience if l != "Present"],
        "education_raw": education, "skills_raw": skills,
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
    }
