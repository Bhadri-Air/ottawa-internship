"""Everything you are likely to want to change lives in this file."""

# ---------------------------------------------------------------- target term
# The radar is built around one summer. Bump these for the next cycle.
TARGET_YEAR = 2027
SUMMER_MONTHS = (5, 8)  # May..August, inclusive

# How old (by the employer's own posting date) a role may be and still show.
# Summer co-ops stay open for months, so this is generous. Undated roles are kept.
MAX_AGE_DAYS = 90

# A role first seen within this many days gets a NEW badge.
NEW_BADGE_DAYS = 3

# Drop roles from state.json once they have been gone from every source this long.
FORGET_AFTER_DAYS = 30

# ---------------------------------------------------------------- location
# A role must mention one of these places (or be remote within Canada).
# Names that also exist elsewhere carry ", on" so "New Orleans, LA" or
# "Burlington, VT" don't sneak in. Remove a city here to stop tracking it.
CITIES = {
    "ottawa": [
        "ottawa", "kanata", "nepean", "orléans", "orleans, on", "barrhaven",
        "gloucester, on", "stittsville", "gatineau", "national capital region",
    ],
    "toronto": [
        "toronto", "gta", "greater toronto", "north york", "etobicoke", "scarborough, on",
        "mississauga", "markham", "vaughan", "richmond hill", "brampton", "oakville",
        "pickering, on", "ajax, on", "burlington, on", "thornhill",
    ],
}
CITY_LABELS = {"ottawa": "Ottawa", "toronto": "Toronto", "remote": "Remote (Canada)"}
INCLUDE_REMOTE_CANADA = True

# One-click LinkedIn searches shown at the top of the feed (LinkedIn itself is
# not scraped: its terms forbid it and it blocks automated access).
LINKEDIN_SEARCHES = [
    ("Ottawa", "software intern OR software co-op", "Ottawa, Ontario, Canada"),
    ("Ottawa", "machine learning intern OR AI intern OR AI co-op", "Ottawa, Ontario, Canada"),
    ("Toronto", "software intern OR software co-op", "Toronto, Ontario, Canada"),
    ("Toronto", "machine learning intern OR AI intern OR AI co-op", "Toronto, Ontario, Canada"),
    ("Both", "summer 2027 software intern", "Ontario, Canada"),
]

# ---------------------------------------------------------------- sources
# Community trackers. Simplify-style repos publish a structured listings.json;
# the negarprh repo is a markdown table in its README.
SIMPLIFY_TRACKERS = [
    "SimplifyJobs/Summer2027-Internships",
]
MARKDOWN_TRACKERS = [
    "negarprh/Canadian-Tech-Internships-2027",
]

# Ottawa employers queried directly through their applicant-tracking system.
# platform: workday | lever | greenhouse | ashby
#   workday token: the careers URL, e.g. https://ciena.wd5.myworkdayjobs.com/Careers
#   lever / greenhouse / ashby token: the board slug, e.g. "magnetforensics"
# Add more with:  python radar.py --sniff <careers url>
COMPANIES = [
    {"name": "Ciena",       "platform": "workday", "token": "https://ciena.wd5.myworkdayjobs.com/Careers"},
    {"name": "Entrust",     "platform": "workday", "token": "https://entrust.wd1.myworkdayjobs.com/entrustcareers"},
    {"name": "Lumentum",    "platform": "workday", "token": "https://lumentum.wd5.myworkdayjobs.com/LITE"},
    {"name": "Aptiv",       "platform": "workday", "token": "https://aptiv.wd5.myworkdayjobs.com/aptiv_careers"},
    {"name": "Semtech",     "platform": "workday", "token": "https://semtech.wd1.myworkdayjobs.com/SemtechCareers"},
    {"name": "Marvell",     "platform": "workday", "token": "https://marvell.wd1.myworkdayjobs.com/MarvellCareers"},
    {"name": "NAV CANADA",  "platform": "workday", "token": "https://navcanada.wd10.myworkdayjobs.com/NAV_Careers"},
    {"name": "Magnet Forensics", "platform": "lever", "token": "magnetforensics"},
    # Nokia (Oracle), Kinaxis (iCIMS), Ross Video, Shopify and General Dynamics
    # have no simple public API; their postings still arrive through the trackers.

    # ---- Toronto / GTA
    {"name": "Cohere",        "platform": "ashby",      "token": "cohere"},
    {"name": "Wealthsimple",  "platform": "ashby",      "token": "wealthsimple"},
    {"name": "Waabi",         "platform": "lever",      "token": "waabi"},
    {"name": "BenchSci",      "platform": "lever",      "token": "benchsci"},
    {"name": "Kepler Communications", "platform": "lever", "token": "kepler"},
    {"name": "Achievers",     "platform": "lever",      "token": "achievers"},
    {"name": "Equitable Bank", "platform": "lever",     "token": "eqbank"},
    {"name": "Tenstorrent",   "platform": "greenhouse", "token": "tenstorrentuniversity"},
    {"name": "Faire",         "platform": "greenhouse", "token": "faire"},
    {"name": "DoorDash",      "platform": "greenhouse", "token": "doordashcanada"},
    {"name": "HeyGen",        "platform": "greenhouse", "token": "heygen"},
    {"name": "TD Bank",       "platform": "workday", "token": "https://td.wd3.myworkdayjobs.com/TD_Bank_Careers"},
    {"name": "RBC",           "platform": "workday", "token": "https://rbc.wd3.myworkdayjobs.com/RBCEARLYTALENT1"},
    {"name": "BMO",           "platform": "workday", "token": "https://bmo.wd3.myworkdayjobs.com/External"},
    {"name": "Manulife",      "platform": "workday", "token": "https://manulife.wd3.myworkdayjobs.com/MFCJH_Jobs"},
    {"name": "Intact",        "platform": "workday", "token": "https://intactfc.wd3.myworkdayjobs.com/intactfc"},
    {"name": "Autodesk",      "platform": "workday", "token": "https://autodesk.wd1.myworkdayjobs.com/uni"},
    {"name": "Intel",         "platform": "workday", "token": "https://intel.wd1.myworkdayjobs.com/external"},
    {"name": "Loblaw",        "platform": "workday", "token": "https://myview.wd3.myworkdayjobs.com/paradox_careers"},
]

# Workday search is keyword driven, so each board is searched with each of these.
WORKDAY_QUERIES = ["intern", "co-op", "student"]

HTTP_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (compatible; ottawa-internship-radar/1.0)"
