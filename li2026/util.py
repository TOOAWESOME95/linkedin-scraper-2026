import random
import re

from . import config

NOISE = {"Contact info", "Follow", "Message", "Connect", "More", "Show all",
         "Save in Sales Navigator", "View my newsletter", "…see more", "see more"}


def clean(lines):
    """Strip blanks, buttons and the duplicate text LinkedIn renders twice."""
    out = []
    for l in (x.strip() for x in lines):
        if not l or l in NOISE or (l.startswith("·") and len(l) < 6):
            continue
        if out and out[-1] == l:
            continue
        out.append(l)
    return out


def profile_url(href):
    """Normalise any /in/ link to https://www.linkedin.com/in/<slug>/"""
    m = re.search(r"linkedin\.com/in/([^/?#]+)", href or "") or re.match(r"/in/([^/?#]+)", href or "")
    return f"https://www.linkedin.com/in/{m.group(1)}/" if m else None


def read_urls(path=None):
    path = path or config.URLS
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"{p} not found. Run:  py li.py collect   (or create it, one URL per line)")
    seen, out = set(), []
    for line in p.read_text(encoding="utf-8").splitlines():
        u = profile_url(line.strip())
        if u and u not in seen:
            seen.add(u); out.append(u)
    return out


def pause(rng):
    return random.uniform(*rng)
