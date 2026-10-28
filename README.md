# Unit Club

A responsive Monash unit review app, with a mobile layout and home-screen manifest. This is a local web MVP, not a native iOS/Android build or production service.

## Run

Requires Python 3.10+ and curl. No package installation required.

```sh
python3 server.py
```

Open http://localhost:8000. The server binds to localhost. Unit data is read from `data/units.json`; submitted reviews persist in `data/reviews.sqlite3`. Bookmarks stay in the browser. Demo reviews are generated separately, visibly labelled, and never saved to the review database. Switch off **Demo reviews** to see only submitted reviews.

## Monash data

```sh
python3 importer.py                     # import starter units
python3 importer.py --codes FIT1045     # refresh specific units
python3 importer.py --all --year 2026   # discover all units in Monash's sitemap
```

The importer extracts CourseLoop records embedded in public Monash Handbook pages. It stores the source URL and import timestamp, checks record shape, rate limits sequential requests, retries network failures, and checkpoints each successful record. Failed imports do not delete previous data. Full discovery can take hours; only the starter catalogue has been imported in this checkout. Review Monash's applicable data-use requirements before operating a recurring production importer. Metadata refresh does not erase reviews. Full imports upsert records; they do not automatically retire units removed from the handbook. This MVP stores one current record per university/unit code; add a unit-year table before supporting multiple handbook years simultaneously.

## Behaviour and model

University ID → faculty name → unit ID. Unit IDs include the university namespace. Catalogue responses include universities; extend that list and add imported records to onboard another institution. The current interface launches with Monash only.

Reviews have an enjoyment score from 1–5, display name, required year taken and semester/teaching period, and text. The top 10 uses average stars, then review count, then code to break ties; unrated units are excluded. Faculty/search filters narrow the university's top 10 without reranking. No minimum review count is imposed in this MVP; low-volume averages are not statistically robust.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

## Before a public launch

Add authenticated student accounts and university email verification, ownership-based review editing, one-review-per-student/unit constraints, reporting/moderation, abuse controls and rate limits, a production HTTPS server, migrations/backups, and a deployed database. Local display names are not verified identities. Add native packaging if App Store/Play Store distribution is desired. The current server is intended for local development only.
