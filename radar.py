"""Ottawa + Toronto Summer internship radar: fetch, filter, dedupe, publish.

  python radar.py            fetch everything and rewrite the README feed
  python radar.py --check    per-source status and the matches, no files written
  python radar.py --html     also write radar.html and open it
  python radar.py --sniff U  work out the config line for a careers page
"""
import argparse
import json
import re
import sys
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import config
import filters
import render
import sources

ROOT = Path(__file__).parent
STATE = ROOT / "state.json"
README = ROOT / "README.md"

_SUFFIX = re.compile(r"\b(inc|ltd|llc|corp|corporation|limited|ulc|plc|co)\b\.?")
_NOISE = re.compile(r"\([^)]*\)|\b(winter|spring|summer|fall)\s*20\d\d\b|\b\d+\s*months?\b|"
                    r"\bco-?\s?op\b|\bcoop\b|\binternship\b|\bintern\b|\bstudent\b|[^a-z0-9 ]")


def fingerprint(company, title):
    """Same role from two sources -> same key. Word order and term labels are ignored."""
    c = _SUFFIX.sub("", company.lower())
    c = re.sub(r"[^a-z0-9]", "", c)
    words = sorted(w for w in _NOISE.sub(" ", title.lower()).split() if w and not w.isdigit())
    return f"{c}:{' '.join(words)}"


def _is_tracker(p):
    return p["uid"].startswith(("simplify:", "md:"))


def fetch_all():
    results, health = [], []
    srcs = sources.all_sources()
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [(name, pool.submit(fn)) for name, fn in srcs]
        for name, fut in futures:
            try:
                rows = fut.result()
                results.extend(rows)
                health.append({"name": name, "ok": True, "count": len(rows), "error": ""})
            except Exception as e:  # one broken board never fails the run
                health.append({"name": name, "ok": False, "count": 0, "error": f"{type(e).__name__}: {e}"})
    return results, health


def classify(postings, now):
    keep, by_url = {}, {}
    cutoff = now - config.MAX_AGE_DAYS * 86400
    for p in postings:
        loc = filters.location_match(p["location"])
        if not loc or not filters.is_student_role(p["title"]):
            continue
        role = filters.role_type(p["title"])
        if not role:
            continue
        term = filters.classify_term(p["title"], p.get("terms"))
        if not term:
            continue
        if p.get("posted") and p["posted"] < cutoff:
            continue
        fp = fingerprint(p["company"], p["title"])
        # The same apply link under two titles is the same job.
        url_key = re.sub(r"[?#].*$", "", p["url"]).rstrip("/").lower()
        fp = by_url.setdefault(url_key, fp) if url_key else fp
        p = dict(p, loc=loc, role=role, term=term, fp=fp)
        prev = keep.get(fp)
        if prev is None:
            keep[fp] = p
            continue
        # Prefer the clearer term, then the employer's own board over a tracker.
        rank = {"summer": 0, "covers": 1, "unstated": 2}
        better_term = rank[term] < rank[prev["term"]]
        replaces_tracker = _is_tracker(prev) and not _is_tracker(p)
        if better_term or (rank[term] == rank[prev["term"]] and replaces_tracker):
            p["posted"] = p.get("posted") or prev.get("posted")
            keep[fp] = p
    order = {"summer": 0, "covers": 1, "unstated": 2}
    return sorted(keep.values(), key=lambda p: (order[p["term"]], -(p.get("posted") or 0), p["company"].lower()))


def update_state(matches, now):
    state = json.loads(STATE.read_text()) if STATE.exists() else {"seeded": False, "jobs": {}}
    seeded_run = not state.get("seeded")
    jobs = state.setdefault("jobs", {})
    for p in matches:
        entry = jobs.setdefault(p["fp"], {"first_seen": now, "seed": seeded_run})
        entry["last_seen"] = now
        fresh = now - entry["first_seen"] < config.NEW_BADGE_DAYS * 86400
        p["new"] = fresh and not entry.get("seed")
    forget = now - config.FORGET_AFTER_DAYS * 86400
    state["jobs"] = {k: v for k, v in jobs.items() if v.get("last_seen", 0) >= forget}
    state["seeded"] = True
    return state


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--sniff", metavar="URL")
    args = ap.parse_args(argv)

    if args.sniff:
        found = sources.sniff(args.sniff)
        if not found:
            print("No supported job platform found on that page.")
            return 1
        print(json.dumps({"name": "Company Name", **found}) + ",")
        return 0

    now = int(time.time())
    raw, health = fetch_all()
    matches = classify(raw, now)

    if args.check:
        for h in health:
            print(f"{'ok  ' if h['ok'] else 'FAIL'} {h['name']:<45} {h['count'] if h['ok'] else h['error']}")
        print(f"\n{len(raw)} postings fetched, {len(matches)} Ottawa + Toronto software/AI matches\n")
        for p in matches:
            print(f"[{p['term']:<8}] [{p['role']:<3}] {p['company']} · {p['title']}\n           {p['url']}")
        return 0

    state = update_state(matches, now)
    feed = render.build_feed(matches, health, now)
    text, changed = render.splice(README.read_text() if README.exists() else "", feed)
    if changed:
        README.write_text(text)
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n")
    print(f"{len(matches)} matches · README {'updated' if changed else 'unchanged'}")

    failed = sum(1 for h in health if not h["ok"])
    if failed > len(health) * 0.5:
        print(f"WARNING: {failed}/{len(health)} sources failed", file=sys.stderr)

    if args.html:
        out = ROOT / "radar.html"
        out.write_text(render.build_html(matches, now))
        webbrowser.open(out.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
