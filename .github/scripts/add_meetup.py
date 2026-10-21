"""Turn an approved "Submit a meetup" issue into a meetups.json entry.

Reads the issue body from the ISSUE_BODY environment variable (never from
the command line, so submitted text can't be interpreted by the shell).
Writes a comment for the issue to result.md and sets the step output
`status` to `added` or `rejected`.
"""

import json
import os
import re
import sys

from meetup_rules import LABEL_TO_CATEGORY, check_entry, ordered, same_meetup

DATA_FILE = os.environ.get("MEETUPS_FILE", "meetups.json")

# Issue-form headings -> JSON fields (must match new-meetup.yml labels)
HEADINGS = {
    "meetup name": "name",
    "category": "category",
    "focus / topic": "type",
    "website url": "website",
    "city": "city",
    "country": "country",
    "schedule": "schedule",
    "latitude (optional)": "lat",
    "longitude (optional)": "lng",
    "description (optional)": "description",
}


def parse_issue(body):
    fields = {}
    for section in re.split(r"^###\s+", body.replace("\r\n", "\n"), flags=re.M)[1:]:
        heading, _, value = section.partition("\n")
        key = HEADINGS.get(heading.strip().lower())
        if not key:
            continue
        value = value.strip()
        if value == "_No response_":
            value = ""
        fields[key] = value
    return fields


def build_entry(fields):
    entry = {k: v for k, v in fields.items() if k not in ("lat", "lng") and v}
    if "category" in entry:
        entry["category"] = LABEL_TO_CATEGORY.get(entry["category"].lower(), entry["category"])
    for coord in ("lat", "lng"):
        raw = fields.get(coord, "")
        try:
            entry[coord] = round(float(raw), 4)
        except ValueError:
            entry[coord] = raw or None
    return ordered(entry)


def finish(status, message):
    with open("result.md", "w", encoding="utf-8") as f:
        f.write(message)
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a", encoding="utf-8") as f:
        f.write(f"status={status}\n")
    print(message)
    sys.exit(0)


def main():
    body = os.environ.get("ISSUE_BODY", "")
    entry = build_entry(parse_issue(body))

    problems = check_entry(entry)
    if entry.get("lat") is None or entry.get("lng") is None:
        problems = [p for p in problems if not p.startswith(("`lat`", "`lng`"))]
        problems.append("no map location: edit the issue and fill in Latitude and Longitude "
                        "(right-click the spot in Google Maps to copy them)")
    if problems:
        finish("rejected",
               "⚠️ Couldn't add this meetup yet:\n\n"
               + "\n".join(f"- {p}" for p in dict.fromkeys(problems))
               + "\n\nEdit the issue to fix this, then remove and re-add the `approved` label.")

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    meetups = data.setdefault("meetups", [])

    if any(same_meetup(entry, existing) for existing in meetups):
        finish("rejected",
               f"⚠️ **{entry['name']}** in {entry['city']} is already on the map, so nothing was added. "
               "Edit `meetups.json` directly if the existing entry needs updating.")

    meetups.append(entry)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    finish("added",
           f"✅ Added **{entry['name']}** to the map. It'll show up once the site redeploys "
           "(usually within a few minutes). Thanks for contributing!\n\n"
           "```json\n" + json.dumps(entry, indent=2, ensure_ascii=False) + "\n```")


if __name__ == "__main__":
    main()
