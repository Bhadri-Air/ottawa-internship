"""Fetchers. Each returns a list of Posting dicts and raises on failure.

A Posting is a plain dict:
  uid       stable id from the provider (never an index)
  company, title, location, url
  terms     extra text that may carry the work term (tracker term columns)
  posted    unix timestamp of the provider's posting date, or None
  source    human-readable source name
"""
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

import config

# ------------------------------------------------------------------ http

def _request(url, data=None, headers=None, attempts=3):
    hdrs = {"User-Agent": config.USER_AGENT, "Accept": "application/json, text/plain, */*"}
    if data is not None:
        hdrs["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    hdrs.update(headers or {})
    delay = 2
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs)
            with urllib.request.urlopen(req, timeout=config.HTTP_TIMEOUT) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                wait = e.headers.get("Retry-After")
                time.sleep(int(wait) if wait and wait.isdigit() else delay)
                delay *= 2
                continue
            raise
        except urllib.error.URLError:
            if attempt < attempts - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def get_json(url, data=None):
    return json.loads(_request(url, data=data))


# ------------------------------------------------------------------ trackers

def simplify_tracker(repo):
    """Simplify-family repos keep structured data in .github/scripts/listings.json."""
    last = None
    for branch in ("dev", "main"):
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/.github/scripts/listings.json"
        try:
            rows = get_json(url)
            break
        except urllib.error.HTTPError as e:
            last = e
    else:
        raise last
    out = []
    for r in rows:
        if not r.get("active", True) or not r.get("is_visible", True):
            continue
        out.append({
            "uid": f"simplify:{r.get('id')}",
            "company": r.get("company_name", ""),
            "title": r.get("title", ""),
            "location": " | ".join(r.get("locations") or []),
            "url": r.get("url", ""),
            "terms": ", ".join(r.get("terms") or []),
            "posted": r.get("date_posted"),
            "source": repo.split("/")[-1],
        })
    return out


_MD_LINK = re.compile(r"\]\((https?://[^)\s]+)\)")
_HTML_LINK = re.compile(r'href="(https?://[^"]+)"')


def _parse_date(text):
    text = (text or "").strip()
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%b %d %Y"):
        try:
            return int(datetime.strptime(text, fmt).replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            pass
    return None


def parse_markdown_table(md, source):
    """Parse a 'Company | Role | Location | Apply | Date' pipe table, handling ↳ rows."""
    out, header, company = [], None, ""
    for line in md.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        lowered = [c.lower() for c in cells]
        if "company" in lowered and any(h in lowered for h in ("role", "position", "title")):
            header = lowered
            continue
        if header is None or set(line) <= set("|-: "):
            continue
        row = dict(zip(header, cells))
        name = row.get("company", "")
        if name in ("↳", "") and company:
            name = company
        company = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", name).strip("* ")
        apply_cell = row.get("apply", row.get("link", ""))
        # The Apply cell is usually a badge: [![Apply](badge-image)](real-url).
        links = [u for u in _MD_LINK.findall(apply_cell) + _HTML_LINK.findall(apply_cell)
                 if "shields.io" not in u and not u.endswith((".png", ".svg"))]
        if not links:  # "Closed🔒" or no link
            continue
        link = links[-1]
        title = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", row.get("role", row.get("position", row.get("title", ""))))
        out.append({
            "uid": f"md:{link}",
            "company": company,
            "title": title.strip("* "),
            "location": row.get("location", ""),
            "url": link,
            "terms": "",
            "posted": _parse_date(row.get("date posted", row.get("date", ""))),
            "source": source,
        })
    return out


def markdown_tracker(repo):
    last = None
    for branch in ("main", "dev", "master"):
        try:
            md = _request(f"https://raw.githubusercontent.com/{repo}/{branch}/README.md")
            return parse_markdown_table(md, repo.split("/")[-1])
        except urllib.error.HTTPError as e:
            last = e
    raise last


# ------------------------------------------------------------------ ATS adapters

_WD_AGO = re.compile(r"posted\s+(\d+)\+?\s+days?\s+ago", re.I)


def _workday_posted(text):
    text = (text or "").lower()
    now = time.time()
    if "today" in text:
        return int(now)
    if "yesterday" in text:
        return int(now - 86400)
    m = _WD_AGO.search(text)
    return int(now - int(m.group(1)) * 86400) if m else None


def workday(company):
    base = company["token"].rstrip("/")
    u = urlparse(base)
    tenant = u.netloc.split(".")[0]
    site = u.path.strip("/").split("/")[-1]
    api = f"{u.scheme}://{u.netloc}/wday/cxs/{tenant}/{site}/jobs"
    seen = {}
    for query in config.WORKDAY_QUERIES:
        offset = 0
        while offset < 400:
            page = get_json(api, data={"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": query})
            jobs = page.get("jobPostings") or []
            for j in jobs:
                path = j.get("externalPath", "")
                req = (j.get("bulletFields") or [path])[0]
                seen[req] = {
                    "uid": f"workday:{tenant}:{req}",
                    "company": company["name"],
                    "title": j.get("title", ""),
                    "location": j.get("locationsText", ""),
                    "url": f"{u.scheme}://{u.netloc}/{site}{path}",
                    "terms": "",
                    "posted": _workday_posted(j.get("postedOn")),
                    "source": company["name"],
                }
            if len(jobs) < 20:
                break
            offset += 20
    return list(seen.values())


def lever(company):
    rows = get_json(f"https://api.lever.co/v0/postings/{company['token']}?mode=json")
    return [{
        "uid": f"lever:{r['id']}",
        "company": company["name"],
        "title": r.get("text", ""),
        "location": " | ".join(filter(None, [(r.get("categories") or {}).get("location", "")]
                                      + (r.get("categories") or {}).get("allLocations", []))),
        "url": r.get("hostedUrl", ""),
        "terms": (r.get("categories") or {}).get("commitment", ""),
        "posted": int(r["createdAt"] / 1000) if r.get("createdAt") else None,
        "source": company["name"],
    } for r in rows]


def greenhouse(company):
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{company['token']}/jobs")
    out = []
    for r in data.get("jobs", []):
        posted = r.get("first_published") or r.get("updated_at")
        out.append({
            "uid": f"greenhouse:{r['id']}",
            "company": company["name"],
            "title": r.get("title", ""),
            "location": (r.get("location") or {}).get("name", ""),
            "url": r.get("absolute_url", ""),
            "terms": "",
            "posted": int(datetime.fromisoformat(posted.replace("Z", "+00:00")).timestamp()) if posted else None,
            "source": company["name"],
        })
    return out


def ashby(company):
    data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{company['token']}")
    out = []
    for r in data.get("jobs", []):
        locs = [r.get("location", "")] + [s.get("location", "") for s in r.get("secondaryLocations") or []]
        posted = r.get("publishedAt")
        out.append({
            "uid": f"ashby:{r['id']}",
            "company": company["name"],
            "title": r.get("title", ""),
            "location": " | ".join(filter(None, locs)) + (" | Remote Canada" if r.get("isRemote") else ""),
            "url": r.get("jobUrl", ""),
            "terms": r.get("employmentType", ""),
            "posted": int(datetime.fromisoformat(posted.replace("Z", "+00:00")).timestamp()) if posted else None,
            "source": company["name"],
        })
    return out


ADAPTERS = {"workday": workday, "lever": lever, "greenhouse": greenhouse, "ashby": ashby}


def all_sources():
    """(name, zero-arg fetch function) for every configured source."""
    out = []
    for repo in config.SIMPLIFY_TRACKERS:
        out.append((f"{repo.split('/')[-1]} [tracker]", lambda r=repo: simplify_tracker(r)))
    for repo in config.MARKDOWN_TRACKERS:
        out.append((f"{repo.split('/')[-1]} [tracker]", lambda r=repo: markdown_tracker(r)))
    for c in config.COMPANIES:
        out.append((f"{c['name']} [{c['platform']}]", lambda c=c: ADAPTERS[c["platform"]](c)))
    return out


# ------------------------------------------------------------------ sniffer

def sniff(url):
    """Guess the platform and token for a careers URL, printing a config line."""
    host = urlparse(url).netloc.lower()
    if "myworkdayjobs.com" in host:
        return {"platform": "workday", "token": url.split("?")[0].rstrip("/")}
    for platform, marker in (("lever", "lever.co"), ("greenhouse", "greenhouse.io"), ("ashby", "ashbyhq.com")):
        if marker in host:
            slug = urlparse(url).path.strip("/").split("/")
            slug = slug[-1] if platform == "greenhouse" and "boards" in host and len(slug) == 1 else slug[0]
            return {"platform": platform, "token": slug}
    page = _request(url)
    for platform, pat in (
        ("workday", r"https://[\w.-]+\.myworkdayjobs\.com/[\w-]+"),
        ("lever", r"jobs\.lever\.co/([\w-]+)"),
        ("greenhouse", r"(?:boards|job-boards)\.greenhouse\.io/(?:embed/job_board\?for=)?([\w-]+)"),
        ("ashby", r"jobs\.ashbyhq\.com/([\w-]+)"),
    ):
        m = re.search(pat, page)
        if m:
            return {"platform": platform, "token": m.group(1) if m.groups() else m.group(0)}
    return None
