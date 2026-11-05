"""Paths and safety settings. Edit here to change pacing and daily limits."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

SESSION = DATA / "session.json"          # your LinkedIn login (never commit this)
URLS = DATA / "urls.txt"                 # one profile URL per line
CONNECTIONS_CSV = DATA / "connections.csv"
PROFILES_JSON = DATA / "profiles.json"
PROFILES_CSV = DATA / "profiles.csv"
VISITED_CSV = DATA / "visited.csv"       # shared memory: who has been visited and when
DEBUG_DIR = DATA / "debug"

# --- safety -----------------------------------------------------------------
REVISIT_DAYS = 14            # never touch the same person again within this window
SCRAPE_MAX_PER_RUN = 80      # profiles scraped per run (override with --max)
VISIT_MAX_PER_RUN = 50       # profiles visited per run (override with --max)
SCRAPE_DELAY = (20, 45)      # seconds between scraped profiles (random)
VISIT_DELAY = (25, 70)       # seconds between visited profiles (random)
HEADLESS = False             # visible browser is less likely to be flagged
VIEWPORT = {"width": 1280, "height": 900}
