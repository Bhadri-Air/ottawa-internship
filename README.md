# Ottawa + Toronto Summer 2027 Internship Radar

[![radar](../../actions/workflows/radar.yml/badge.svg)](../../actions/workflows/radar.yml)

A self-updating list of **Summer 2027 software developer and AI/ML co-ops and internships in Ottawa and Toronto**:
Ottawa, Kanata, Nepean, Orléans, Barrhaven and Gatineau; Toronto and the GTA (Mississauga, Markham, Vaughan,
Richmond Hill, Brampton, Oakville, North York, Etobicoke, Scarborough); plus roles that are remote within Canada.
Each role is tagged with its city.
GitHub Actions re-checks every source every 4 hours and rewrites the list below. Free: no paid APIs,
no accounts, no secrets, and no third-party Python packages.

Roles are sorted into three groups:

- **☀️ Summer 2027**: the posting names Summer 2027.
- **📅 Runs through summer**: a longer term that includes May to August 2027 (Jan to Aug, Jan to Dec, Winter 2027 plus 8 months, and so on).
- **❓ Term not stated**: a live software/AI student role that doesn't say when it runs. Apply and ask.

The top of the feed also has one-click **LinkedIn searches** (Ottawa and Toronto, internship level, past 7
days). LinkedIn itself isn't scraped: its terms forbid automated scraping and it blocks bots, so the radar
gives you pre-filtered search links instead.

Anything that names only another term (Winter 2027 for 4 months, Fall 2026, Fall 2027) is left out.
🆕 marks roles first seen in the last 3 days.

---

## The feed

Everything between the markers is generated. Don't edit it by hand.

<!-- RADAR:START -->
<!-- RADAR:END -->

---

## Setup (about 5 minutes)

1. Create a new **public** repository on GitHub (public repos get unlimited free Actions minutes).
2. Upload every file from this folder, keeping the `.github/workflows/radar.yml` path.
3. Go to **Settings → Actions → General → Workflow permissions** and pick **Read and write permissions**.
4. Go to **Actions → radar → Run workflow**. After a minute or two the feed above fills in.

From then on it runs by itself. GitHub doesn't send notifications for commits, so bookmark the repo
page and check the 🆕 rows.

GitHub pauses scheduled workflows after 60 days with no commits. The radar's own commits count, so an
active feed keeps itself alive; if it ever stops, press **Run workflow** once.

## Running it on your laptop

Python 3.10 or newer, nothing to install:

```
python radar.py --check    # every source ok/FAIL, then every match with its apply link
python radar.py --html     # also builds radar.html and opens it in your browser
python -m unittest discover -s tests
```

## Changing what it looks for

Everything is in [`config.py`](config.py):

| Setting | What it does |
| --- | --- |
| `TARGET_YEAR` | The summer to look for. Change to 2028 next year. |
| `CITIES` | The cities tracked and the place names that count for each. Delete a city to stop tracking it. |
| `LINKEDIN_SEARCHES` | The LinkedIn search links shown at the top of the feed. |
| `INCLUDE_REMOTE_CANADA` | Keep roles that are remote within Canada. |
| `MAX_AGE_DAYS` | Hide postings older than this (by the employer's posting date). |
| `COMPANIES` | Ottawa and Toronto employers checked directly. |

### Adding a company

```
python radar.py --sniff https://some-company.com/careers
```

It prints a line to paste into `COMPANIES`. Supported platforms: Workday, Lever, Greenhouse, Ashby.
Then run `python radar.py --check` to make sure it works.

## How it works

| File | What's in it |
| --- | --- |
| `config.py` | All settings and the company list |
| `sources.py` | Fetchers: Simplify `listings.json`, markdown tracker tables, Workday, Lever, Greenhouse, Ashby |
| `filters.py` | Which city? Is it a student role? Software or AI? Which term? |
| `radar.py` | Runs every source in parallel, filters, removes duplicates, writes the feed |
| `render.py` | Builds the README tables (with safe escaping) and the local HTML page |
| `state.json` | When each role was first seen, for the 🆕 badge. Small, committed by the workflow |
| `tests/` | Unit tests; the workflow runs them before every publish |

**Sources.** Two community trackers (Simplify's Summer 2027 list and Canadian Tech Internships 2027)
plus Ottawa and Toronto employers' own job boards. A broken source is shown as FAIL in *Source health* and never
stops the run.

**Duplicates.** The same job often appears in several places. Two postings are merged if they have the
same apply link, or the same company and the same title once term labels, "co-op/intern" and word order
are ignored. When merging, the clearer term wins, and the employer's own board wins over a tracker.

**Known gaps.** Nokia (Oracle), Kinaxis (iCIMS), Ross Video, Shopify and General Dynamics don't have a
simple public jobs API, so their roles only show up when a tracker lists them. Some job boards block
cloud servers, which shows up as FAIL in *Source health*. The term is read from the title and tracker
fields, not the full description, so some long co-ops land in *Term not stated*.
