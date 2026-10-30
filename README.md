# LunchTable website

A responsive university unit review website with a desktop landing page, university directory, searchable faculty catalogue, saved units, and a separate top 10 for each university. Navigation stays at the top on desktop and mobile. There is no installable-app manifest or native app build.

## Deploy on GitHub Pages

The root `index.html` is ready for branch-based GitHub Pages hosting. Assets and catalogue requests use relative paths, so both `username.github.io/repository/` and custom domains work. `.nojekyll` disables Jekyll processing. No Node build or Python runtime is required on Pages.

1. Commit and push this folder to GitHub.
2. In the repository, open **Settings → Pages**.
3. Choose **Deploy from a branch**, select your branch (currently `main`), and select **/(root)**.
4. Save and wait for the Pages deployment to finish.

**Reviews on GitHub Pages are browser-local.** They persist on the same browser/device but are not published to other visitors. Rankings use those local reviews (and optional labelled demo ratings). Clearing browser storage removes them. A shared community review service needs a separately hosted backend; GitHub Pages cannot run Python or SQLite.

## Folder layout

```text
index.html              Website entry point
assets/                 Styles, JavaScript, icon, static runtime configuration
data/catalog.json       Generated public catalogue used by GitHub Pages
data/                   Source catalogue snapshots and import status
tools/                 Optional local server, catalogue import/export scripts
tests/                 Data and deployment checks
.nojekyll               GitHub Pages static-site configuration
```

The previous `public/` directory and regenerable import caches have been removed. Existing review databases are preserved locally and excluded from Git. Public catalogue exports never include reviews.

## Local preview

For the same browser-local behaviour as GitHub Pages, serve the root with any static HTTP server. For example:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

For the optional SQLite-backed review API instead:

```sh
python3 tools/server.py
```

Open http://localhost:8000. Run only one server on that port at a time. The optional server supplies runtime configuration that connects the frontend to its API; static hosting uses `assets/runtime-config.js` with no API configured.

Each new review requires an enjoyment score, display name, year taken, semester/teaching period, and text. Bookmarks stay in the browser. Demo reviews are off by default and never stored as real reviews. Existing SQLite reviews remain in the ignored `data/reviews.sqlite3` file and are available through the optional server.

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
python3 tools/bulk_import.py --university monash --year 2026
python3 tools/bulk_import.py --university deakin --year 2026
python3 tools/bulk_import.py --university rmit --year 2026
python3 tools/importer.py --codes FIT1045
```

Bulk imports cache successful public responses in ignored `data/.cache/`, use four workers with a per-request delay, checkpoint every 25 results, and resume already imported URLs. Access-denied/rate-limit responses stop future bulk runs rather than prompting repeated requests. Current RMIT discovery only covers the first page and is always labelled partial. Melbourne records were collected through the public browser; a repeatable full-catalogue importer is not yet implemented. No unattended job is scheduled.

Existing records are preserved on failures. The importer currently stores one current record per university/unit, not multiple historical handbook editions. For a fresh full refresh, preserve a backup before clearing the corresponding cache and per-university snapshot. Bulk records override the older starter file.

After importing or updating source data, regenerate the static catalogue and commit it:

```sh
python3 tools/build_catalogue.py
```

## Rankings and review scope

Top 10 rankings use average stars, then review count, then code for ties. Unrated units are excluded. Rankings, faculty filters, search, saved units, and review choices are scoped to the selected university. Faculty/search filters narrow that university's top 10 without reranking. No minimum review count is imposed yet. The catalogue renders 24 results at a time with a Show more control.

## Verify

```sh
python3 -m unittest discover -s tests -v
```

## Shared reviews in production

The repository is prepared for Pages but has not been pushed or deployed by this change. For reviews shared across visitors, deploy the optional API behind a production server with persistent storage and HTTPS, configure its URL in `assets/runtime-config.js`, and implement appropriate CORS/authentication. Student verification, moderation/reporting, abuse prevention, and backups remain production work.

## Top 10 page

`top10.html` shows overall rankings and a searchable university-specific ranking. Scores use `(total stars + 5 × global mean) / (review count + 5)`, with five-star count, review count and unit ID as tie-breakers. Unrated units and demo ratings are excluded. The same global prior is used for university rankings. Static hosting uses browser-local reviews; the optional server uses shared reviews. Catalogue coverage remains limited to imported units.

Run ranking checks with `node --test tests/rankings.cjs`.

### Leaderboard demo
Open `top10.html?demo=1` or enable **Test with fictional reviews**. The deterministic fixture creates 396 labelled fictional reviews across 48 units (12 per current university), including small samples, large samples and ties. Demo mode uses only fixtures, never writes them to storage or the server, and links to matching demo reviews in unit details. Disable the toggle to restore real rankings.

## Registering another university

University metadata is registered through `UniversityRegistry.register_university()` in `tools/universities.py`. The API and static exporter read the same registry. Add the university's details there, including a stable lowercase ID, name, short name, HTTPS handbook URL, locations, aliases and optional local logo.

For automatic imports, implement `discover(year) -> list[URL]` and `parse(page, url) -> unit`, then register an `ImportAdapter` in `tools/bulk_import.py`. No new CLI branch or frontend logic is needed. Set `coverage_note` for incomplete discovery and `supported_years` when a source cannot select a year. RMIT currently supports 2026 and only the first public listing page. Melbourne retains its existing catalogue but does not yet have an automated adapter.

```sh
python3 tools/bulk_import.py --list
python3 tools/bulk_import.py --university monash --year 2026
python3 tools/build_catalogue.py
```

Every new parsed unit must include `id` (university-prefixed), `university`, `code`, `name`, `faculty`, `year`, and an HTTPS `source`. Shared validation rejects invalid records and records failures in import status. Missing `description` and `credits` default to empty strings. Source-specific fields are preserved. Empty discovery cannot overwrite an existing catalogue, and resuming against a different year is rejected. Existing cached records are still skipped on resume; this refactor does not add automatic freshness checks or full historical versioning.
