"""Fail if meetups.json is broken, so a bad edit never reaches the live map."""

import json
import os
import sys

from meetup_rules import check_entry, same_meetup

DATA_FILE = os.environ.get("MEETUPS_FILE", "meetups.json")


def main():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"::error file={DATA_FILE},line={e.lineno},col={e.colno}::Invalid JSON: {e.msg}")
        return 1

    meetups = data.get("meetups") if isinstance(data, dict) else None
    if not isinstance(meetups, list):
        print(f'::error file={DATA_FILE}::Top level must be {{"meetups": [ ... ]}}')
        return 1

    errors = 0
    for i, entry in enumerate(meetups):
        label = f"#{i + 1} ({entry.get('name', 'unnamed')})" if isinstance(entry, dict) else f"#{i + 1}"
        if not isinstance(entry, dict):
            print(f"::error file={DATA_FILE}::Entry {label} is not an object")
            errors += 1
            continue
        for problem in check_entry(entry):
            print(f"::error file={DATA_FILE}::Entry {label}: {problem}")
            errors += 1
        for j in range(i):
            if isinstance(meetups[j], dict) and same_meetup(entry, meetups[j]):
                print(f"::warning file={DATA_FILE}::Entry {label} duplicates entry #{j + 1}")

    print(f"Checked {len(meetups)} meetups: {errors} problem(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
