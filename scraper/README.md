# Polite Scraper

## Target classification

- **Site:** Books to Scrape (`books.toscrape.com`), part of the Zyte Web Scraping Sandbox (`toscrape.com`)
- **Why this site is appropriate:** toscrape.com explicitly describes Books to Scrape as "a fictional bookstore that desperately wants to be scraped... a safe place for beginners learning web scraping." The site exists specifically for scraping practice.
- **robots.txt check:** `https://books.toscrape.com/robots.txt` returns `404 Not Found`. No robots file exists. A missing file is not permission by itself, but combined with the site's own stated purpose (a scraping sandbox), proceeding is appropriate here.
- **Scope:** the first 3 catalogue pages only (~60 books), plus each book's own detail page.
- **Data collected:** title, product URL, price, availability, star rating, description, source page, and fetch timestamp, publicly displayed product listing data, no personal or private information.

I will not reuse this code on another site without checking its rules and terms first.