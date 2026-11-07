"""Turn classified postings into the README feed (and an optional local HTML page)."""
import html
import re
from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import config

TZ = ZoneInfo("America/Toronto")
START, END = "<!-- RADAR:START -->", "<!-- RADAR:END -->"
STAMP = re.compile(r"^\*Updated .*\*$", re.M)

SECTIONS = [
    ("summer", "☀️ Summer {y}", "Postings that name Summer {y} as the work term."),
    ("covers", "📅 Runs through summer {y}", "Longer terms (8, 12 or 16 months, Jan to Aug, Jan to Dec) that include May to August {y}."),
    ("unstated", "❓ Term not stated", "Live software/AI student roles that don't say when they run. Apply and ask about summer."),
]


def md_escape(text):
    text = html.escape(str(text or ""), quote=False)
    return text.replace("|", "\\|").replace("\n", " ").replace("[", "\\[").replace("]", "\\]")


def safe_url(url):
    return url if re.match(r"^https?://", url or "") else None


def age_label(ts, now):
    if not ts:
        return "—"
    days = (datetime.fromtimestamp(now, TZ).date() - datetime.fromtimestamp(ts, TZ).date()).days
    return "Today" if days <= 0 else "Yesterday" if days == 1 else f"{days} days ago"


def _row(p, now):
    url = safe_url(p["url"])
    title = md_escape(p["title"])
    role = f"[{title}]({url})" if url else title
    if p.get("new"):
        role = "🆕 " + role
    kind = "🤖 AI/ML" if p["role"] == "ai" else "💻 Software"
    city = config.CITY_LABELS.get(p["loc"], p["loc"].title())
    where = md_escape(p["location"])[:80] if p["loc"] != "remote" else "Remote"
    return f"| {role} | {md_escape(p['company'])} | **{city}** | {where} | {kind} | {age_label(p.get('posted'), now)} |"


def linkedin_url(keywords, location):
    # f_E=1 internship level, f_TPR=r604800 posted in the past week, newest first
    q = {"keywords": keywords, "location": location, "f_E": "1", "f_TPR": "r604800", "sortBy": "DD"}
    return "https://www.linkedin.com/jobs/search/?" + urlencode(q)


def linkedin_block():
    if not getattr(config, "LINKEDIN_SEARCHES", None):
        return []
    links = " · ".join(f"[{md_escape(city)}: {md_escape(kw)}]({linkedin_url(kw, loc)})"
                       for city, kw, loc in config.LINKEDIN_SEARCHES)
    return ["**🔎 LinkedIn, last 7 days (opens a filtered search):** " + links, ""]


def build_feed(postings, health, now):
    y = config.TARGET_YEAR
    stamp = datetime.fromtimestamp(now, TZ).strftime("%A %d %B %Y, %H:%M Eastern")
    ok = sum(1 for h in health if h["ok"])
    counts = " · ".join(f"{config.CITY_LABELS.get(c, c)} {sum(1 for p in postings if p['loc'] == c)}"
                        for c in list(config.CITIES) + ["remote"])
    lines = [f"*Updated {stamp} · {ok}/{len(health)} sources healthy · {len(postings)} roles*", "",
             f"**By city:** {counts}", ""]
    lines += linkedin_block()
    for key, heading, blurb in SECTIONS:
        rows = [p for p in postings if p["term"] == key]
        lines += [f"### {heading.format(y=y)} · {len(rows)}", "", blurb.format(y=y), ""]
        if not rows:
            lines += ["_Nothing right now._", ""]
            continue
        lines += ["| Role | Company | City | Location | Type | Posted |", "| --- | --- | --- | --- | --- | --- |"]
        lines += [_row(p, now) for p in rows]
        lines.append("")
    lines += ["<details><summary>Source health</summary>", "",
              "| Source | Postings | Status |", "| --- | --- | --- |"]
    for h in health:
        status = "ok" if h["ok"] else f"**FAIL** {md_escape(h['error'])[:120]}"
        lines.append(f"| {md_escape(h['name'])} | {h['count'] if h['ok'] else '-'} | {status} |")
    lines += ["", "</details>"]
    return "\n".join(lines)


def splice(readme, feed):
    """Replace the block between the markers. Returns (new_text, changed_ignoring_stamp)."""
    if START not in readme or END not in readme:
        readme = readme.rstrip() + f"\n\n{START}\n{END}\n"
    head, rest = readme.split(START, 1)
    old, tail = rest.split(END, 1)
    new = f"{head}{START}\n{feed}\n{END}{tail}"
    changed = STAMP.sub("", old.strip()) != STAMP.sub("", feed.strip())
    return new, changed


def build_html(postings, now):
    rows = "".join(
        f"<tr><td><a href='{html.escape(p['url'])}'>{html.escape(p['title'])}</a></td>"
        f"<td>{html.escape(p['company'])}</td><td>{config.CITY_LABELS.get(p['loc'], p['loc'])}</td><td>{p['term']}</td><td>{p['role']}</td>"
        f"<td>{age_label(p.get('posted'), now)}</td></tr>"
        for p in postings if safe_url(p["url"])
    )
    return ("<!doctype html><meta charset=utf-8><title>Ottawa radar</title>"
            "<style>body{font:14px system-ui;margin:2rem}td,th{padding:4px 10px;text-align:left}"
            "tr:nth-child(even){background:#8881}</style>"
            "<table><tr><th>Role</th><th>Company</th><th>City</th><th>Term</th><th>Type</th><th>Posted</th></tr>"
            f"{rows}</table>")
