"""Decide whether a posting is an Ottawa, student, software/AI role, and when it runs.

Every function here is pure (text in, answer out) so it is easy to unit test.
"""
import re

import config

# ------------------------------------------------------------------ helpers

def _norm(text):
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


# ------------------------------------------------------------------ student level

_STUDENT = re.compile(r"\b(intern(ship)?s?|co-?\s?op|coop|cooperative education|student|work term|placement|stage|stagiaire)\b")
_NOT_STUDENT = re.compile(r"\b(senior|sr\.?|staff|principal|lead|manager|director|new grad(uate)?|phd researcher)\b")


def is_student_role(title):
    t = _norm(title)
    return bool(_STUDENT.search(t)) and not _NOT_STUDENT.search(t)


# ------------------------------------------------------------------ role type

_AI = re.compile(
    r"\b(ai|a\.i\.|artificial intelligence|machine learning|ml|mlops|deep learning|"
    r"data scien\w*|nlp|llms?|genai|generative|computer vision|neural|agents?|"
    r"applied scientist|research scientist|intelligence artificielle)\b"
)
_SWE = re.compile(
    r"\b(software|developer|d[ée]veloppeu\w*|programm\w*|full[\s-]?stack|back[\s-]?end|"
    r"front[\s-]?end|web|mobile|ios|android|devops|sre|site reliability|cloud|platform|"
    r"firmware|embedded|qa|quality assurance|test automation|automation|tools?|"
    r"data engineer\w*|security engineer\w*|cyber\w*|computer science|swe|sde|"
    r"application|api|infrastructure|systems? engineer\w*)\b"
)
# Clearly not software, even when a word above appears ("Sales Automation Intern").
_OFF_TOPIC = re.compile(
    r"\b(sales|marketing|recruit\w*|human resources|hr|accounting|accountant|finance|"
    r"legal|paralegal|payroll|procurement|supply chain|mechanical|civil|"
    r"analog|asic|pcb|pcba|rf|layout|optical|photonic\w*|technician|electrical engineer)\b"
)


_HARDWARE = re.compile(r"\b(hardware|hw|asic|fpga|silicon|soc|pcb|pcba|analog|optical|photonic\w*)\b")


def role_type(title):
    """Return 'ai', 'swe' or None for a posting title."""
    t = _norm(title)
    if _HARDWARE.search(t) and not re.search(r"\bsoftware\b", t):
        return None
    if _AI.search(t):
        return "ai"
    if _OFF_TOPIC.search(t):
        return None
    if _SWE.search(t):
        return "swe"
    return None


# ------------------------------------------------------------------ location

_REMOTE_CANADA = re.compile(r"remote[^|;]*\b(canada|can)\b|\b(canada|can)\b[^|;]*remote")


def location_match(location):
    """The first matching city key from config.CITIES, 'remote', or None.

    A role listed in both Ottawa and Toronto counts as the city listed first in CITIES.
    """
    loc = _norm(location)
    for city, places in config.CITIES.items():
        if any(re.search(rf"\b{re.escape(p)}\b", loc) for p in places):
            return city
    if config.INCLUDE_REMOTE_CANADA and _REMOTE_CANADA.search(loc):
        return "remote"
    return None


# ------------------------------------------------------------------ work term

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "janvier": 1, "mai": 5, "juin": 6, "juillet": 7, "aout": 8, "août": 8,
}
_MONTH_RE = (r"(january|february|march|april|may|june|july|august|september|october|"
             r"november|december|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec)\b\.?")
_SEASON = re.compile(r"\b(winter|spring|summer|fall|autumn|été|hiver|automne)(?:\s+term)?[\s/-]*'?(20\d{2}|\d{2})\b")
_SHORT = re.compile(r"\b([wsf])'?(2\d)\b")
_RANGE = re.compile(
    rf"\b{_MONTH_RE}\s*(?:,?\s*(20\d{{2}}))?\s*(?:-|–|—|to|through|until)\s*{_MONTH_RE}\s*,?\s*(20\d{{2}})"
)
_DURATION = re.compile(r"\b(4|8|12|16|20)[\s-]*(months?|mois|mo)\b")

_SEASON_START = {"winter": 1, "hiver": 1, "spring": 5, "summer": 5, "été": 5,
                 "fall": 9, "autumn": 9, "automne": 9}


def _year(y):
    y = int(y)
    return y + 2000 if y < 100 else y


def _overlaps_summer(start, end):
    """start/end are (year, month). True when the span covers June-July of the target year."""
    y = config.TARGET_YEAR
    s_lo, s_hi = (y, config.SUMMER_MONTHS[0] + 1), (y, config.SUMMER_MONTHS[1] - 1)
    return start <= s_lo and end >= s_hi


def _add_months(ym, n):
    y, m = ym
    m = m + n - 1
    return (y + (m - 1) // 12, (m - 1) % 12 + 1)


def classify_term(*texts):
    """Classify the work term from a title and any extra term fields.

    Returns one of:
      'summer'   explicitly Summer <target year>
      'covers'   a longer term that runs through the target summer
      'unstated' no term information at all; worth applying and asking
      None       a term was given and it is not the target summer
    """
    t = _norm(" ".join(x for x in texts if x))
    seasons = [(s, _year(y)) for s, y in _SEASON.findall(t)]
    seasons += [({"w": "winter", "s": "summer", "f": "fall"}[s], _year(y)) for s, y in _SHORT.findall(t)]
    durations = [int(d) for d, _ in _DURATION.findall(t)]
    target = config.TARGET_YEAR

    if any(s in ("summer", "été") and y == target for s, y in seasons):
        return "summer"

    # Explicit month ranges: "January - August 2027", "Jan 2027 - Dec 2027"
    ranges = _RANGE.findall(t)
    for m1, y1, m2, y2 in ranges:
        end = (int(y2), _MONTHS[m2[:3]])
        start_year = int(y1) if y1 else (end[0] if _MONTHS[m1[:3]] <= end[1] else end[0] - 1)
        start = (start_year, _MONTHS[m1[:3]])
        if _overlaps_summer(start, end):
            return "covers"

    # A season start plus a duration: "Winter 2027 - 8 months"
    longest = max(durations) if durations else 4
    for s, y in seasons:
        start = (y, _SEASON_START[s])
        end = _add_months(start, longest - 1)
        if _overlaps_summer(start, end):
            return "covers"

    if seasons or ranges:
        return None  # it names terms, and none of them reach the target summer

    # "May 2027" on its own
    if re.search(rf"\b(may|june|july)[a-z]*\.?\s*,?\s*{target}\b", t):
        return "summer"

    # A bare year with no season is too vague to reject.
    if re.search(rf"\b(20[0-2]\d)\b", t) and not re.search(rf"\b{target}\b", t):
        # Only years before the target -> an old cycle.
        years = [int(y) for y in re.findall(r"\b(20[0-2]\d)\b", t)]
        if years and max(years) < target:
            return None
    return "unstated"
