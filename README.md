# Ottawa + Toronto Summer 2027 Internship Radar

[![radar](../../actions/workflows/radar.yml/badge.svg)](../../actions/workflows/radar.yml)

A live feed of **Summer 2027 software developer and AI/ML internships and co-ops
in Ottawa and Toronto**. GitHub Actions re-checks about 200 job boards and
community trackers every 4 hours and rewrites the list below. Free: no paid
APIs, no accounts, no secrets.

What you see:

- **Ottawa and Toronto only.** Ottawa, Kanata, Nepean, Orléans, Barrhaven,
  Stittsville and Gatineau; Toronto and the GTA (Mississauga, Markham, Vaughan,
  Richmond Hill, Brampton, Oakville, North York, Scarborough, ...); plus roles
  that are remote within Canada. Waterloo, Hamilton and the rest of Ontario
  are left out. The **City** column says which city each role is in.
- **Summer 2027 only.** Roles that say Summer 2027, S27 or start in May to
  August 2027 are kept. Winter 2027 (including 8–16 month co-ops that start
  in January), Spring, Fall 2026 and Fall 2027 roles are dropped. Roles that
  don't state a term are kept, since many postings never say: check before
  applying.
- **Fresh postings.** AI/ML roles from the last 14 days, software and tech
  roles from the last 7 days, newest first.
- **🤖 AI/ML** holds roles with AI or ML in the title, or a software title whose
  job description names enough ML terms. **💻 Software & tech** holds the other
  software, data, QA, DevOps and IT student roles.
- **One row per role**, even when the same job appears on several boards.

**🔎 LinkedIn, last 7 days** (LinkedIn can't be scraped, so these open a
pre-filtered search): [Ottawa · software](https://www.linkedin.com/jobs/search/?keywords=software+intern+OR+software+co-op&location=Ottawa%2C+Ontario%2C+Canada&f_E=1&f_TPR=r604800&sortBy=DD) · [Ottawa · AI/ML](https://www.linkedin.com/jobs/search/?keywords=machine+learning+intern+OR+AI+intern+OR+AI+co-op&location=Ottawa%2C+Ontario%2C+Canada&f_E=1&f_TPR=r604800&sortBy=DD) · [Toronto · software](https://www.linkedin.com/jobs/search/?keywords=software+intern+OR+software+co-op&location=Toronto%2C+Ontario%2C+Canada&f_E=1&f_TPR=r604800&sortBy=DD) · [Toronto · AI/ML](https://www.linkedin.com/jobs/search/?keywords=machine+learning+intern+OR+AI+intern+OR+AI+co-op&location=Toronto%2C+Ontario%2C+Canada&f_E=1&f_TPR=r604800&sortBy=DD) · [Summer 2027 · Ontario](https://www.linkedin.com/jobs/search/?keywords=summer+2027+software+intern&location=Ontario%2C+Canada&f_E=1&f_TPR=r604800&sortBy=DD)

---

## The feed

Everything between the markers is generated. Don't edit it by hand.

<!-- radar:listings:start -->
<!-- radar:listings:end -->

---

## Setup

1. Put these files in a **public** GitHub repo (Actions minutes are free and
   unlimited only on public repos).
2. **Settings → Actions → General → Workflow permissions → Read and write
   permissions → Save.**
3. **Actions → radar → Run workflow**, choose mode **`seed`**, and run it.
   This records everything currently live, so postings with no publish date
   show as *date unknown* instead of all looking new today.
4. Run it once more with mode **`run`**. The feed above fills in, and from then
   on the schedule keeps it updated.

GitHub pauses scheduled workflows after 60 days with no commits. The radar's
own feed commits count, so an active feed keeps itself alive.

## Changing what it looks for

| What | Where |
| --- | --- |
| Target term (move to Summer 2028 next year) | `TARGET_CYCLES` in [companies.py](companies.py) |
| How many days a role stays listed | `MAX_AGE_HOURS` and `STRICT_MAX_AGE_HOURS` in [companies.py](companies.py) |
| Which places count as Ottawa or Toronto | `_OTTAWA_TERMS` and `_TORONTO_TERMS` in [core.py](core.py) |
| How often it runs | the `cron` line in [.github/workflows/radar.yml](.github/workflows/radar.yml) |
| Companies checked directly | `COMPANIES` in [companies.py](companies.py) |

Run the tests after any change: `python -m unittest discover -s tests`.

## Running it on your computer

```
pip install -r requirements.txt
python -m playwright install chromium
python radar.py --check     # every source ok/FAIL, plus recent matches
python radar.py --open      # build radar.html and open it
python radar.py --reasons   # why postings were dropped
```

## Adding companies

Point the sniffer at a careers page:

```bash
python radar.py --sniff https://www.some-company.com/careers
```

It prints a line ready to paste into `COMPANIES` in
[companies.py](companies.py):

```
    {"name": "Some Company", "platform": "greenhouse", "token": "somecompany", "ai_native": False},
```

Set `ai_native: True` when *every* engineering role at the company is an AI
role. A generic title like "Software Engineer Intern" at an `ai_native`
company then lands in the AI/ML section.

Then confirm before trusting it: `python radar.py --check`.

A careers page that draws its list in the browser gets `browser: True` and
the page URL as `token`. The radar opens it in Chromium, then reads the same
`JobPosting` data or job links as any other HTML source. Point `token` at the
search results (internships, Ottawa or Toronto), not the marketing homepage.

```
    {"name": "Some Portal", "platform": "html", "token": "https://jobs.example.com/search?q=intern", "ai_native": False, "browser": True},
```

Company-hosted SuccessFactors career sites (`/search/?q=...`) are read
directly: the token is the site's own search URL, narrowed to Ontario. Only
the older `careerN.successfactors.com` hosted sites get an HTML-fallback line
from the sniffer.

When the careers page is rendered client-side or sits behind Cloudflare, the
sniffer sees nothing. Guess the token instead — the ATS APIs are usually still
reachable even when the company's own site is not:

```bash
python radar.py --probe deepgenomics deep-genomics
```

It tries each slug on Ashby, Greenhouse, Lever, SmartRecruiters, Workable,
BambooHR and JazzHR, and prints a paste-ready line for every board that has postings. An empty board
counts as a miss: SmartRecruiters answers 200 with an empty list for any slug.

### Workday

Workday tokens cannot be guessed; the tenant and site slugs rarely match the
company name. Sniffing the careers URL itself usually works:

```bash
python radar.py --sniff https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite
```

If it does not, copy the real one from the browser: DevTools → **Network**,
filter **Fetch/XHR**, search for a job, find the POST whose URL contains
`/wday/cxs/`, and use that full URL (it ends in `/jobs`) as the `token`.

A posting URL already in the feed works too: in
`https://rbc.wd3.myworkdayjobs.com/RBCEARLYTALENT1/job/...` the tenant is `rbc`
and the site is `RBCEARLYTALENT1`, so the token is
`https://rbc.wd3.myworkdayjobs.com/wday/cxs/rbc/RBCEARLYTALENT1/jobs`. That is
how the RBC, TD, CIBC, BMO and Manulife boards were added.

---

## License

MIT License. See [LICENSE](LICENSE).
