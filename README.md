# Unit Club website

A responsive university unit review website with a desktop landing page, university directory, searchable faculty catalogue, saved units, and a separate top 10 for each university. Navigation stays at the top on desktop and mobile. There is no installable-app manifest or native app build.

## Local preview

Requires Python 3.10+; importers also use curl. No package installation is required.

```sh
python3 server.py
```

Open http://localhost:8000. If the existing preview server is running, open that URL rather than starting a second server on the same port.

Submitted reviews persist in `data/reviews.sqlite3`. Each new review requires an enjoyment score, display name, year taken, semester/teaching period, and text. Older reviews retain their original period labels. Bookmarks stay in the browser. Demo reviews are off by default, explicitly labelled, restricted to the original Monash sample units, and never stored in the database.

## Catalogue coverage — 2026

The website merges the original `data/units.json` with per-university JSON catalogues by stable, university-prefixed IDs. Coverage notices disclose incomplete imports. The status files record discovery counts and failures; the public API omits raw error lists.

| University | Loaded records | Coverage |
| --- | ---: | --- |
| Monash | 211 | 17 original records plus 194 from the full import. The sitemap yielded 5,224 URLs; later requests returned HTTP 403. Incomplete. |
| Melbourne | 254 | A subset of Architecture, Building and Planning subjects collected from the public browser results. The full search reports 6,221 subjects. Incomplete; descriptions are linked to the handbook instead of invented. |
| RMIT | 50 | First public course-results page. Anonymous APEX pagination returned an expired-session response. Full pagination remains outstanding. |
| Deakin | 1,858 | All unique URLs returned across the 2026 unit-level searches were imported successfully. This measures discovered URLs, not an independently verified university-wide total. |

RMIT uses colleges/schools; these appear in the common faculty filter. RMIT IDs preserve the handbook's internal course identifier while the display code uses available offering codes. Deakin faculties use its [official unit-code convention](https://www.deakin.edu.au/students/enrolment-and-fees/enrol/enrolment-codes-and-terminology); nonstandard codes without a known mapping remain explicitly unclassified. Some handbook listings may include unavailable or historical offerings: consult the source before enrolment.

## Importing

```sh
python3 bulk_import.py --university monash --year 2026
python3 bulk_import.py --university deakin --year 2026
python3 bulk_import.py --university rmit --year 2026
python3 importer.py --codes FIT1045
```

Bulk imports cache successful public responses in ignored `data/.cache/`, use four workers with a per-request delay, checkpoint every 25 results, and resume already imported URLs. Access-denied/rate-limit responses stop future bulk runs rather than prompting repeated requests. Current RMIT discovery only covers the first page and is always labelled partial. Melbourne records were collected through the public browser; a repeatable full-catalogue importer is not yet implemented. No unattended job is scheduled.

Existing records are preserved on failures. The importer currently stores one current record per university/unit, not multiple historical handbook editions. For a fresh full refresh, preserve a backup before clearing the corresponding cache and per-university snapshot. Bulk records override the older starter file.

## Rankings and review scope

Top 10 rankings use average stars, then review count, then code for ties. Unrated units are excluded. Rankings, faculty filters, search, saved units, and review choices are scoped to the selected university. Faculty/search filters narrow that university's top 10 without reranking. No minimum review count is imposed yet. The catalogue renders 24 results at a time with a Show more control.

## Verify

```sh
python3 -m unittest discover -s tests -v
```

## Public hosting

This checkout runs a local development website; it has not been deployed publicly. GitHub can host the source, but GitHub Pages cannot run the Python review API or SQLite database. Public launch requires a production Python host with persistent storage, HTTPS, student authentication, moderation/reporting, abuse prevention, and backups. Display names are not verified identities.
