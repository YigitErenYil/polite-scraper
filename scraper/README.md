# Polite Scraper

A small, polite scraping pipeline: it downloads the first three catalogue pages of Books to Scrape, visits all 60 book pages, turns messy HTML into clean, checked JSON records, survives a broken page without crashing, and ends every run with a short report of what happened.

## Target classification

- **Site:** Books to Scrape (`books.toscrape.com`), part of the Zyte Web Scraping Sandbox (`toscrape.com`)
- **Why this site is appropriate:** toscrape.com explicitly describes Books to Scrape as "a fictional bookstore that desperately wants to be scraped... a safe place for beginners learning web scraping." The site exists specifically for scraping practice.
- **robots.txt check:** `https://books.toscrape.com/robots.txt` returns `404 Not Found`. No robots file exists. A missing file is not permission by itself, but combined with the site's own stated purpose (a scraping sandbox), proceeding is appropriate here.
- **Scope:** the first 3 catalogue pages only (~60 books), plus each book's own detail page.
- **Data collected:** title, product URL, price, availability, star rating, description, source page, and fetch timestamp — publicly displayed product listing data, no personal or private information.

I will not reuse this code on another site without checking its rules and terms first.

## Lane & setup

Python 3.10+.

```bash
pip install -r requirements.txt
```

Dependencies: `requests` (HTTP), `beautifulsoup4` (HTML parsing), `pydantic` (schema validation).

## Run it

```bash
python src/main.py
```

First run fetches everything from the live site (3 catalogue pages + 60 book pages) and caches it under `cache/`. Every subsequent run reads from the cache instead of hitting the site again — you'll see `CACHE HIT` instead of `FETCH` in the output.

Output:
- `output/books.json` — the validated records
- `output/errors.json` — any records that failed schema validation, with the reason
- `output/run-report.json` — a summary of the run

## Record schema

Each record in `books.json` has these fields:

| Field | Type | Notes |
|---|---|---|
| `title` | string | Book title |
| `product_url` | string | Absolute URL, used as the record's canonical identity |
| `price_gbp` | number | Parsed from `price_text`, e.g. `51.77` |
| `price_text` | string | Original price text as shown on the page, e.g. `£51.77` |
| `availability_text` | string | e.g. `In stock (22 available)` |
| `rating_text` | string or null | e.g. `Three` |
| `description` | string or null | `null` when the book has no description — never invented |
| `source_page` | string | Which catalogue page this book was discovered on |
| `fetched_at` | string | ISO 8601 UTC timestamp of when the detail page was fetched |

Records are keyed by `product_url` before being written, so re-running the scraper never produces duplicates — `books.json` always holds exactly 60 unique records.

## Politeness rules

- **User-agent:** every real request identifies itself as `FlyRankInternshipA9/1.0 (+https://github.com/YigitErenYil/polite-scraper)`.
- **Timeout:** every request gives up after 10 seconds — never waits forever.
- **Delay:** at least 0.5 seconds between real requests to the site. Cached pages need no delay — they never leave this computer.
- **Cache:** every fetched page is saved to `cache/` and reused on subsequent runs, so the site is only asked once per page during development.
- **Status check:** only a `200` response is treated as a successful fetch.
- **Failure handling:** if a single book page fails (e.g. a broken or missing URL), it's logged and skipped — the run finishes and the other valid records are still written.

## Example run report

```json
{
  "start_time": "2026-09-16T12:23:06.936727Z",
  "end_time": "2026-09-16T12:23:07.564622Z",
  "duration_seconds": 0.63,
  "catalogue_pages_fetched": 3,
  "book_pages_attempted": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

## Why no browser was needed

The product title, price, availability, rating, and description are all present in the raw HTML the server sends back — nothing on this site is rendered client-side with JavaScript. Requesting the page with a plain HTTP library and parsing the HTML is sufficient; a full browser (e.g. Playwright) would only add startup cost, memory overhead, and complexity with no benefit for this target.

## Ethics note

Use an official API when one exists instead of scraping. Never bypass logins, paywalls, or explicit blocks (a `403` or a disallow rule in `robots.txt` means stop, not retry). Collect only the data actually needed for the task, and identify the scraper honestly via its user-agent so a site owner can always tell who made the request.

## Extras: CSV export

`output/books.csv` is generated from the same validated records as `books.json`. No values needed flattening — every field in the schema is already a flat string, number, or null, so the conversion is a direct field-by-field write. `null` values (missing `rating_text` or `description`) appear as empty cells in the CSV.

## Extras: Tiny dashboard

`output/dashboard.html` is a static snapshot regenerated on every run — no server, no JavaScript, just an HTML file written directly from Python using the same `valid_records` and `run-report.json` data already produced by the pipeline. It shows record count, price range, failed pages, invalid records, and when the data was last refreshed. Open it in any browser after running the scraper.