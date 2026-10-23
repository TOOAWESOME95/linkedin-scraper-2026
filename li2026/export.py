"""profiles.json -> profiles.csv (one row per person)."""
import csv
import json
import re

from . import config

DATE = re.compile(r"((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+)?\d{4}\s*[-–]\s*"
                  r"(Present|((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+)?\d{4})", re.I)
DUR = re.compile(r"^(\w+-time\s*·\s*)?\d+\s+(yrs?|mos?)\b", re.I)
LOCISH = re.compile(r"(United Kingdom|United States|England|Scotland|Wales|Ireland|On-site|Remote|Hybrid)", re.I)
SKIP = {"Present", "Full-time", "Part-time", "Self-employed", "Freelance", "Contract", "Internship"}


def current_role(exp):
    """(title, company) of the current job. Handles both layouts:
       single role:   Title / Company · Full-time / dates
       grouped roles: Company / 5 yrs 4 mos / Title / dates"""
    for i, l in enumerate(exp or []):
        if DATE.search(l) and "Present" in l:
            block = exp[:i]
            grouped = any(DUR.match(x) for x in block)
            cand = [x.split(" · ")[0].strip() for x in block
                    if x not in SKIP and not DATE.search(x) and not DUR.match(x) and not LOCISH.search(x)]
            cand = [c for c in cand if c and c not in SKIP]
            if not cand:
                return "", ""
            if grouped:
                return cand[-1], cand[0]
            return (cand[-2], cand[-1]) if len(cand) >= 2 else (cand[-1], "")
    return "", ""


def export():
    if not config.PROFILES_JSON.exists():
        raise SystemExit("No profiles.json yet. Run:  py li.py scrape")
    data = json.loads(config.PROFILES_JSON.read_text(encoding="utf-8"))
    tidy = lambda xs: [x for x in (xs or []) if x not in SKIP]
    rows = []
    for p in data.values():
        title, company = current_role(p.get("experience_raw"))
        rows.append({
            "name": p.get("name") or "", "headline": p.get("headline") or "",
            "location": p.get("location") or "",
            "current_title": title, "current_company": company,
            "email": p.get("email") or "", "phone": p.get("phone") or "",
            "websites": " | ".join(p.get("websites") or []),
            "experience": " | ".join(tidy(p.get("experience_raw"))),
            "education": " | ".join(tidy(p.get("education_raw"))),
            "skills": " | ".join(tidy(p.get("skills_raw"))),
            "about": p.get("about") or "", "profile_url": p.get("url") or "",
            "scraped_at": p.get("scraped_at") or "",
        })
    with config.PROFILES_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"✓ {len(rows)} rows written to {config.PROFILES_CSV}")
