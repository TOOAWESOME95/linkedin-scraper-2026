"""visited.csv - shared memory so no script touches the same person twice too soon."""
import csv
from datetime import datetime, timedelta

from . import config


def recent(days=None):
    days = config.REVISIT_DAYS if days is None else days
    if not config.VISITED_CSV.exists():
        return set()
    cutoff = datetime.now() - timedelta(days=days)
    with config.VISITED_CSV.open(encoding="utf-8") as f:
        return {r["url"] for r in csv.DictReader(f)
                if datetime.fromisoformat(r["visited_at"]) > cutoff}


def log(url, action, status="ok"):
    new = not config.VISITED_CSV.exists()
    with config.VISITED_CSV.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["url", "visited_at", "action", "status"])
        w.writerow([url, datetime.now().isoformat(timespec="seconds"), action, status])
