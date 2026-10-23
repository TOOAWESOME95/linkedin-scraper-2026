#!/usr/bin/env python3
"""
linkedin-scraper-2026 - one command for everything.

  py li.py login                     log in once, saves data/session.json
  py li.py collect [--max N]         your connections -> data/urls.txt + connections.csv
  py li.py scrape  [--max N] [--refresh] [--no-contact] [--file F]
  py li.py contacts [--max N]        fetch email/phone for people already scraped
  py li.py visit   [--max N] [--file F]   view profiles (they see you in "Who viewed")
  py li.py export                    data/profiles.json -> data/profiles.csv
  py li.py status                    what's been collected / scraped / visited
"""
import argparse
import asyncio
import json
import sys

from li2026 import config, memory, __version__


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # ✓/✗ on Windows consoles
    ap = argparse.ArgumentParser(prog="li.py", description=f"linkedin-scraper-2026 v{__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login")
    c = sub.add_parser("collect"); c.add_argument("--max", type=int)
    s = sub.add_parser("scrape"); s.add_argument("--max", type=int); s.add_argument("--file")
    s.add_argument("--refresh", action="store_true"); s.add_argument("--no-contact", action="store_true")
    ct = sub.add_parser("contacts"); ct.add_argument("--max", type=int); ct.add_argument("--file")
    v = sub.add_parser("visit"); v.add_argument("--max", type=int); v.add_argument("--file")
    sub.add_parser("export"); sub.add_parser("status")
    a = ap.parse_args()

    if a.cmd == "login":
        from li2026.browser import login; asyncio.run(login())
    elif a.cmd == "collect":
        from li2026.connections import collect; asyncio.run(collect(a.max))
    elif a.cmd == "scrape":
        from li2026.runner import scrape
        asyncio.run(scrape(a.file, a.max, a.refresh, not a.no_contact))
    elif a.cmd == "contacts":
        from li2026.runner import contacts_only; asyncio.run(contacts_only(a.file, a.max))
    elif a.cmd == "visit":
        from li2026.runner import visit; asyncio.run(visit(a.file, a.max))
    elif a.cmd == "export":
        from li2026.export import export; export()
    elif a.cmd == "status":
        url_list = config.URLS.read_text(encoding="utf-8").split() if config.URLS.exists() else []
        urls = len(url_list)
        prof = json.loads(config.PROFILES_JSON.read_text(encoding="utf-8")) if config.PROFILES_JSON.exists() else {}
        emails = sum(1 for p in prof.values() if p.get("email"))
        print(f"Session:      {'yes' if config.SESSION.exists() else 'NO - run: py li.py login'}")
        print(f"Connections:  {urls} in {config.URLS.name}")
        print(f"Scraped:      {len(prof)} profiles ({emails} with email)")
        print(f"Touched in last {config.REVISIT_DAYS} days: {len(memory.recent())}")
        if urls:
            print(f"Still to scrape: {sum(1 for u in url_list if u not in prof)}")


if __name__ == "__main__":
    main()
