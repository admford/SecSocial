"""Shared rules for meetups.json entries, used by both workflows."""

from urllib.parse import urlparse

CATEGORIES = {
    "social": "Social",
    "conference": "Conference",
    "organization": "Organization / chapter",
    "student": "Student group",
    "tech": "General tech",
    "community": "Makerspace / community",
}
LABEL_TO_CATEGORY = {label.lower(): key for key, label in CATEGORIES.items()}

REQUIRED_TEXT = ["name", "category", "city", "country", "website", "schedule", "type"]
MAX_LEN = {"name": 120, "type": 80, "city": 80, "country": 80, "schedule": 160,
           "website": 300, "description": 1000}

# Key order used when writing entries, to match the existing file
FIELD_ORDER = ["name", "category", "city", "country", "lat", "lng",
               "website", "schedule", "type", "description"]


def check_entry(entry):
    """Return a list of problems with one entry (empty list means it's valid)."""
    problems = []
    for field in REQUIRED_TEXT:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"`{field}` is missing")
    for field, limit in MAX_LEN.items():
        value = entry.get(field)
        if isinstance(value, str) and len(value) > limit:
            problems.append(f"`{field}` is longer than {limit} characters")

    if entry.get("category") and entry["category"] not in CATEGORIES:
        problems.append(f"`category` must be one of: {', '.join(CATEGORIES)}")

    website = entry.get("website")
    if isinstance(website, str) and website:
        parsed = urlparse(website)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            problems.append("`website` must be a full http:// or https:// address")

    for field, low, high in (("lat", -90, 90), ("lng", -180, 180)):
        value = entry.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            problems.append(f"`{field}` must be a number")
        elif not low <= value <= high:
            problems.append(f"`{field}` must be between {low} and {high}")

    unknown = set(entry) - set(FIELD_ORDER)
    if unknown:
        problems.append(f"unknown field(s): {', '.join(sorted(unknown))}")
    return problems


def ordered(entry):
    return {k: entry[k] for k in FIELD_ORDER if k in entry}


def same_meetup(a, b):
    def norm(s):
        return " ".join(str(s or "").lower().split())
    return norm(a.get("name")) == norm(b.get("name")) and norm(a.get("city")) == norm(b.get("city"))
