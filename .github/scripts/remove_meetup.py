"""Remove the meetup named in an approved "Request a removal" issue.

Reads the issue body from the ISSUE_BODY environment variable. Finds the
entry by name and city (case- and whitespace-insensitive), and only removes
it when exactly one entry matches. Writes a comment for the issue to
result.md and sets the step output `status` to `removed` or `rejected`.
"""

import json
import os
import re
import sys

from meetup_rules import same_meetup

DATA_FILE = os.environ.get("MEETUPS_FILE", "meetups.json")

# Issue-form headings -> fields (must match remove-meetup.yml labels)
HEADINGS = {
    "meetup name": "name",
    "city": "city",
    "reason": "reason",
    "details (optional)": "details",
}


def parse_issue(body):
    fields = {}
    for section in re.split(r"^###\s+", body.replace("\r\n", "\n"), flags=re.M)[1:]:
        heading, _, value = section.partition("\n")
        key = HEADINGS.get(heading.strip().lower())
        if not key:
            continue
        value = value.strip()
        fields[key] = "" if value == "_No response_" else value
    return fields


def finish(status, message):
    with open("result.md", "w", encoding="utf-8") as f:
        f.write(message)
    with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a", encoding="utf-8") as f:
        f.write(f"status={status}\n")
    print(message)
    sys.exit(0)


def main():
    request = parse_issue(os.environ.get("ISSUE_BODY", ""))
    if not request.get("name") or not request.get("city"):
        finish("rejected",
               "⚠️ This request is missing the meetup name or city, so nothing was removed. "
               "Edit the issue to add them, then remove and re-add the `approved` label.")

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    meetups = data.get("meetups", [])

    matches = [i for i, m in enumerate(meetups) if isinstance(m, dict) and same_meetup(m, request)]

    if not matches:
        finish("rejected",
               f"⚠️ No meetup called **{request['name']}** in **{request['city']}** is on the map, "
               "so nothing was removed. It may already be gone, or the name or city in the issue "
               "doesn't exactly match the map. Edit the issue to match, then remove and re-add the "
               "`approved` label, or edit `meetups.json` directly.")
    if len(matches) > 1:
        finish("rejected",
               f"⚠️ {len(matches)} entries match **{request['name']}** in **{request['city']}**, "
               "so nothing was removed automatically. Edit `meetups.json` directly to pick the right one.")

    removed = meetups.pop(matches[0])
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    reason = request.get("reason") or "not given"
    finish("removed",
           f"🗑️ Removed **{removed.get('name')}** ({removed.get('city')}) from the map. "
           f"Reason: {reason}. It'll disappear once the site redeploys (usually within a few minutes).\n\n"
           "If this was a mistake, add this entry back to `meetups.json`:\n\n"
           "```json\n" + json.dumps(removed, indent=2, ensure_ascii=False) + "\n```")


if __name__ == "__main__":
    main()
