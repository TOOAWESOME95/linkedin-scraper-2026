"""Offline tests for the parsers (no LinkedIn access needed).  Run:  py -m pytest"""
import asyncio

from li2026.export import current_role
from li2026.profile import parse_topcard, parse_details_text, parse_contact, card_lines
from li2026.util import clean, profile_url


def test_profile_url_normalises():
    assert profile_url("/in/jane-doe-123/?miniProfile=x") == "https://www.linkedin.com/in/jane-doe-123/"
    assert profile_url("https://uk.linkedin.com/in/jane") == "https://www.linkedin.com/in/jane/"
    assert profile_url("/company/acme/") is None


def test_clean_dedupes_and_drops_buttons():
    assert clean(["Jane", "Jane", "", "Follow", "· 2nd", "Engineer"]) == ["Jane", "Engineer"]


def test_topcard_location_not_headline():
    top = ["Jane Doe", "Head of Growth, Acme and Founder, Beta", "Acme + 2 more",
           "Manchester, England, United Kingdom", "Acme + 2 more", "500+ connections"]
    assert parse_topcard(top, "Jane Doe") == ("Jane Doe", "Head of Growth, Acme and Founder, Beta",
                                               "Manchester, England, United Kingdom")


def test_details_stop_at_sidebar():
    lines = ["Skills", "SEO", "Google Ads", "More profiles for you", "Someone", "Accessibility"]
    assert parse_details_text(lines) == ["SEO", "Google Ads"]
    assert parse_details_text(["Skills that Jane adds will appear here.", "More profiles for you"]) == []


def test_contact_panel():
    text = "Contact Info\nWebsite\nacme.co.uk\nPhone\n07700 900123 (Mobile)\nEmail\njane@example.com"
    hrefs = ["https://www.linkedin.com/in/jane", "https://acme.co.uk/", "mailto:jane@example.com"]
    assert parse_contact(text, hrefs) == {"email": "jane@example.com", "phone": "07700 900123",
                                          "websites": ["https://acme.co.uk/"]}


def test_current_role_single_layout():
    exp = ["Head of Marketing", "Dark Horse", "Oct 2024 - Present · 2 yrs 1 mo", "Present",
           "Digital Marketing Lead", "Pilot Group Ltd · Full-time", "Oct 2022 - Sep 2024 · 2 yrs"]
    assert current_role(exp) == ("Head of Marketing", "Dark Horse")


def test_current_role_grouped_layout():
    exp = ["The Candidate Recruitment Agency", "5 yrs 4 mos", "Associate Director", "Full-time",
           "Jan 2026 - Present · 10 mos", "Manchester, England, United Kingdom"]
    assert current_role(exp) == ("Associate Director", "The Candidate Recruitment Agency")


def test_current_role_with_location_line():
    exp = ["Oscar", "Full-time · 3 mos", "Manchester, England, United Kingdom · On-site",
           "Recruitment Consultant", "Oct 2026 - Present · 1 mo"]
    assert current_role(exp) == ("Recruitment Consultant", "Oscar")


FIXTURE = """<main>
<section componentkey="com.linkedin.sdui.profile.card.refABCTopcard">
  <h2 class="kxhk4p">Jane Doe</h2><p>· 2nd</p>
  <p>Founder, Acme</p><p>Acme</p><p>Leeds, England, United Kingdom</p><a>Contact info</a>
</section>
<section componentkey="com.linkedin.sdui.profile.card.refABCAbout">
  <h2>About</h2><span>Builds things.</span><span style="display:none">hidden script text try again later</span>
</section></main>"""


def test_cards_from_componentkeys():
    from playwright.async_api import async_playwright

    async def run():
        async with async_playwright() as pw:
            b = await pw.chromium.launch()
            page = await b.new_page()
            await page.set_content(FIXTURE)
            top = await card_lines(page, "Topcard")
            about = await card_lines(page, "About")
            await b.close()
            return top, about
    top, about = asyncio.run(run())
    assert parse_topcard(top, "Jane Doe") == ("Jane Doe", "Founder, Acme", "Leeds, England, United Kingdom")
    assert about == ["About", "Builds things."]
