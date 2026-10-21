"""Build meetups.html, a plain list of every meetup, from meetups.json.

The page needs no JavaScript, so search engines can index every meetup
and anyone who can't use the map can still browse them. Run it from the
repo root:  python3 .github/scripts/build_list.py

The output only changes when the data changes (no timestamps), so the
workflows commit it only when there's something new.
"""

import json
import os
import re
from collections import defaultdict
from html import escape
from urllib.parse import urlparse

from meetup_rules import CATEGORIES

DATA_FILE = os.environ.get("MEETUPS_FILE", "meetups.json")
OUT_FILE = os.environ.get("LIST_FILE", "meetups.html")
SITE = "https://sec.social"
REPO = "https://github.com/admford/SecSocial"
GOATCOUNTER = "https://secsocial.goatcounter.com/count"

COLORS = {
    "social": "#d69e2e",
    "conference": "#e53e3e",
    "organization": "#3182ce",
    "student": "#38a169",
    "tech": "#805ad5",
    "community": "#3fd3d5",
}

# Different spellings of the same country are listed together
COUNTRY_ALIASES = {
    "usa": "United States", "us": "United States", "u.s.": "United States",
    "u.s.a.": "United States", "united states of america": "United States",
    "united states": "United States",
    "uk": "United Kingdom", "u.k.": "United Kingdom", "great britain": "United Kingdom",
    "england": "United Kingdom",
}


def country_name(raw):
    raw = " ".join(str(raw or "").split())
    return COUNTRY_ALIASES.get(raw.lower(), raw) or "Unknown"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "x"


def safe_url(value):
    try:
        parsed = urlparse(str(value or ""))
    except ValueError:
        return None
    return value if parsed.scheme in ("http", "https") and parsed.netloc else None


def sort_key(text):
    return " ".join(str(text or "").split()).casefold()


def meetup_html(m):
    key = m.get("category", "")
    label = CATEGORIES.get(key, "Other")
    color = COLORS.get(key, "#718096")
    name = escape(m.get("name", "Unnamed"))
    url = safe_url(m.get("website"))
    title = (f'<a href="{escape(url)}" rel="noopener ugc" target="_blank">{name}</a>'
             if url else name)

    rows = []
    if m.get("type"):
        rows.append(f"<dt>Focus</dt><dd>{escape(m['type'])}</dd>")
    if m.get("schedule"):
        rows.append(f"<dt>Schedule</dt><dd>{escape(m['schedule'])}</dd>")
    rows.append(f"<dt>Location</dt><dd>{escape(m.get('city', ''))}, {escape(m.get('country', ''))}</dd>")
    if url:
        host = urlparse(url).netloc.removeprefix("www.")
        rows.append(f'<dt>Website</dt><dd><a href="{escape(url)}" rel="noopener ugc" target="_blank">{escape(host)}</a></dd>')

    desc = f"\n          <p>{escape(m['description'])}</p>" if m.get("description") else ""
    return f"""        <article class="meetup">
          <h4>{title} <span class="badge" style="--c:{color}">{escape(label)}</span></h4>
          <dl>{''.join(rows)}</dl>{desc}
        </article>"""


def build(meetups):
    by_country = defaultdict(lambda: defaultdict(list))
    for m in meetups:
        if isinstance(m, dict):
            city = " ".join(str(m.get("city") or "Unknown").split())
            by_country[country_name(m.get("country"))][city].append(m)

    countries = sorted(by_country, key=sort_key)
    total = sum(len(ms) for cities in by_country.values() for ms in cities.values())
    cat_counts = defaultdict(int)
    for m in meetups:
        if isinstance(m, dict):
            cat_counts[m.get("category")] += 1
    cat_summary = ", ".join(f"{cat_counts[k]} {CATEGORIES[k].lower()}"
                            for k in CATEGORIES if cat_counts.get(k))

    toc = "\n".join(
        f'        <li><a href="#{slug(c)}">{escape(c)}</a> '
        f'<span class="count">{sum(len(v) for v in by_country[c].values())}</span></li>'
        for c in countries)

    sections = []
    for c in countries:
        city_blocks = []
        for city in sorted(by_country[c], key=sort_key):
            items = "\n".join(meetup_html(m) for m in sorted(by_country[c][city], key=lambda m: sort_key(m.get("name"))))
            city_blocks.append(f'      <section class="city" id="{slug(c)}-{slug(city)}">\n'
                               f"        <h3>{escape(city)}</h3>\n{items}\n      </section>")
        sections.append(f'    <section class="country" id="{slug(c)}">\n'
                        f"      <h2>{escape(c)}</h2>\n" + "\n".join(city_blocks) + "\n    </section>")

    desc = (f"All {total} cybersecurity and tech meetups, conferences, chapters, student groups "
            f"and makerspaces on sec.social, listed by country and city.")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Generated from meetups.json by .github/scripts/build_list.py. Don't edit by hand: changes are overwritten. -->
  <title>All meetups · sec.social</title>
  <meta name="description" content="{escape(desc)}">
  <link rel="canonical" href="{SITE}/meetups.html">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="sec.social">
  <meta property="og:url" content="{SITE}/meetups.html">
  <meta property="og:title" content="All meetups · sec.social">
  <meta property="og:description" content="{escape(desc)}">
  <meta name="twitter:card" content="summary">
  <style>
    :root {{ --ink: #2d3748; --muted: #718096; --line: #e2e8f0; --accent: #667eea; --bg: #f7fafc; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
           color: var(--ink); background: var(--bg); line-height: 1.5; }}
    header {{ background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%); color: white; padding: 32px 16px; text-align: center; }}
    header h1 {{ margin: 0 0 8px; font-size: 2rem; }}
    header p {{ margin: 0; opacity: 0.9; }}
    header a {{ color: #c3dafe; }}
    main {{ max-width: 900px; margin: 0 auto; padding: 24px 16px 48px; }}
    a {{ color: var(--accent); }}
    .toc {{ background: white; border: 1px solid var(--line); border-radius: 10px; padding: 16px 20px; margin-bottom: 32px; }}
    .toc h2 {{ margin: 0 0 8px; font-size: 1rem; }}
    .toc ul {{ display: flex; flex-wrap: wrap; gap: 8px 20px; list-style: none; margin: 0; padding: 0; }}
    .count {{ color: var(--muted); font-size: 0.85rem; }}
    .country > h2 {{ font-size: 1.6rem; border-bottom: 2px solid var(--line); padding-bottom: 6px; margin: 40px 0 8px; }}
    .city > h3 {{ font-size: 1.15rem; margin: 24px 0 8px; color: #4a5568; }}
    .meetup {{ background: white; border: 1px solid var(--line); border-radius: 10px; padding: 14px 18px; margin: 10px 0; }}
    .meetup h4 {{ margin: 0 0 8px; font-size: 1.05rem; }}
    .meetup h4 a {{ color: var(--ink); text-decoration: none; }}
    .meetup h4 a:hover {{ text-decoration: underline; }}
    .badge {{ display: inline-block; vertical-align: middle; margin-left: 6px; padding: 1px 9px; border-radius: 999px;
              background: var(--c); color: white; font-size: 0.72rem; font-weight: 600; }}
    dl {{ display: grid; grid-template-columns: max-content 1fr; gap: 2px 12px; margin: 0; font-size: 0.92rem; }}
    dt {{ color: var(--muted); }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    .meetup p {{ margin: 8px 0 0; color: #4a5568; font-size: 0.92rem; }}
    footer {{ text-align: center; color: var(--muted); font-size: 0.85rem; padding: 24px 16px 40px; }}
    @media (max-width: 600px) {{ dl {{ grid-template-columns: 1fr; }} dt {{ margin-top: 4px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>All meetups</h1>
    <p>{total} meetups in {len(countries)} countries: {escape(cat_summary)}.</p>
    <p><a href="/">← Back to the map</a> · <a href="/#meetupForm">Submit a meetup</a></p>
  </header>
  <main>
    <nav class="toc" aria-label="Countries">
      <h2>Jump to a country</h2>
      <ul>
{toc}
      </ul>
    </nav>
{chr(10).join(sections)}
  </main>
  <footer>
    <p>Spotted something out of date? Open the meetup on the <a href="/">map</a> and choose "Request removal", or <a href="{REPO}/issues">open an issue</a>.</p>
    <p>Meetup data © sec.social contributors, licensed under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license">CC BY 4.0</a>.
       If you reuse it, credit <a href="{REPO}">sec.social (github.com/admford/SecSocial)</a>.</p>
  </footer>
  <script data-goatcounter="{GOATCOUNTER}" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        meetups = json.load(f).get("meetups", [])
    html = build(meetups)
    try:
        with open(OUT_FILE, encoding="utf-8") as f:
            if f.read() == html:
                print(f"{OUT_FILE} is already up to date.")
                return
    except FileNotFoundError:
        pass
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT_FILE} with {len(meetups)} meetups.")


if __name__ == "__main__":
    main()
