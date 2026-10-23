# linkedin-scraper-2026

Tools for **your own LinkedIn network**, rebuilt for LinkedIn's **2026 profile layout**
(the "SDUI" pages with scrambled CSS class names, `<h2>` names and lazy-loaded sections),
where older scrapers like `joeyism/linkedin_scraper` return `Unknown` / empty results.

| Command | What it does |
|---|---|
| `login` | Log in once in a real browser window (2FA works); saves your session |
| `collect` | Reads your **connections** page → list of profile URLs + names/headlines |
| `scrape` | Visits each profile and extracts name, headline, location, about, experience, education, skills, and email/phone/websites (if shared with connections) |
| `contacts` | Fetches just email/phone for people you've already scraped |
| `visit` | Simply views profiles so you appear in their *Who viewed your profile* |
| `export` | Rebuilds the **CSV** (scrape already keeps it updated) |
| `run` | Does it all: collect connections, scrape the next batch, update the CSV |
| `status` | Shows what's collected, scraped and still to do |

It **remembers** everyone it has touched (`data/visited.csv`), so re-running never
hits the same person twice within 14 days, and daily caps keep the pace human.

---

## How it stays working when LinkedIn changes

LinkedIn's 2026 pages use random class names (`kxhk4p kxhkz3 …`) that change often.
This project ignores classes completely and instead finds sections by LinkedIn's own
`componentkey` labels (`…Topcard`, `…About`, `profileCards…`) and section headings,
reads **visible text only**, and falls back to the `/details/experience/` style pages
when a lazy section doesn't render.

---

## Setup (Windows)

You need **Python 3.10+** and **Git**.

```bat
git clone https://github.com/TOOAWESOME95/linkedin-scraper-2026.git
cd linkedin-scraper-2026
py -m pip install -r requirements.txt
py -m playwright install chromium
```

> On Windows use `py` (not `python3`/`pip3`). On macOS/Linux use `python3`.

Then log in once:

```bat
py li.py login
```

A browser opens - log in to LinkedIn normally (including any 2FA). When your feed
loads, the session is saved to `data/session.json` and you're done.

---

## Everyday use

The simplest way: one command, once a day.

```bat
py li.py run
```

This collects **all** your connections, scrapes the next 80 people not yet done,
and keeps `data/profiles.csv` updated after every profile (so if you stop it
halfway, the CSV still has everyone done so far). Run it again tomorrow and it
carries on where it left off.

Or step by step:

```bat
py li.py collect              :: get all your connections (or --max 50 to test)
py li.py scrape               :: scrape the next 80 not yet done (updates the CSV)
py li.py status               :: see progress
```

Run `run` (or `scrape`) once a day until `status` shows nothing left. Other options:

```bat
py li.py scrape --max 30              :: smaller batch
py li.py scrape --no-contact          :: skip the Contact info panel (faster)
py li.py scrape --refresh             :: re-scrape people already done
py li.py scrape --file my_list.txt    :: your own list of profile URLs
py li.py contacts                     :: add emails to people scraped before
py li.py visit --max 40               :: just view profiles, no scraping
```

---

## Folder structure

```
linkedin-scraper-2026/
├── li.py                 ← the only file you run
├── li2026/
│   ├── config.py         ← limits, delays, file paths (edit here)
│   ├── browser.py        ← login + session + "am I blocked?" checks
│   ├── connections.py    ← collect: your connections list
│   ├── profile.py        ← scrape: parsing the 2026 profile layout
│   ├── runner.py         ← batch jobs: scrape / contacts / visit
│   ├── memory.py         ← visited.csv - who was touched and when
│   ├── export.py         ← profiles.json → profiles.csv
│   └── util.py
├── data/                 ← ALL your output lives here (git-ignored)
│   ├── session.json      ← your login - keep private
│   ├── urls.txt          ← from collect
│   ├── connections.csv   ← from collect
│   ├── profiles.json     ← from scrape (raw)
│   ├── profiles.csv      ← from export
│   └── visited.csv       ← memory
└── tests/
```

## Output columns (`profiles.csv`)

`name, headline, location, current_title, current_company, email, phone, websites,
experience, education, skills, about, profile_url, scraped_at`

Experience/education/skills keep LinkedIn's visible lines joined by ` | `, and
`current_title` / `current_company` are worked out from them (both LinkedIn layouts are handled:
a single role, and several roles grouped under one company).

## Safety settings

All in `li2026/config.py`:

| Setting | Default | Meaning |
|---|---|---|
| `SCRAPE_MAX_PER_RUN` | 80 | profiles per `scrape` run |
| `VISIT_MAX_PER_RUN` | 50 | profiles per `visit` run |
| `SCRAPE_DELAY` | 20–45 s | random wait between profiles |
| `VISIT_DELAY` | 25–70 s | random wait between visits |
| `REVISIT_DAYS` | 14 | never touch the same person again within this |
| `HEADLESS` | False | visible browser (less likely to be flagged) |

If LinkedIn shows a security check, login wall or CAPTCHA, every command **stops
immediately**. Clear it in your normal browser and leave it for a day.

**For visits to count**, set LinkedIn → Settings → Visibility → *Profile viewing
options* → **Your name and headline**.

## Troubleshooting

| Problem | Fix |
|---|---|
| `'pip' is not recognized` | use `py -m pip …` |
| `Executable doesn't exist … chrome.exe` | `py -m playwright install chromium` |
| `No session found` | `py li.py login` |
| Logged out / blocked | `py li.py login` again; slow down; wait 24h |
| Experience comes back empty | a copy of the page is saved in `data/debug/`, so open an issue with it |

Moving from `joeyism/linkedin_scraper`? Copy your `linkedin_session.json` to
`data/session.json`, as the format is the same.

## Responsible use

This automates a logged-in browser, which is against LinkedIn's User Agreement and
can get an account restricted, so keep the default limits. It only reads what *you*
can already see as a logged-in member. Contact details are only collected where a
connection has chosen to share them with their network; in the UK/EU, using
personal email addresses for marketing is covered by GDPR and PECR. You are
responsible for how you use it.

## Licence

MIT
