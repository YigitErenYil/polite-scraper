import os
import time
from urllib.parse import urljoin
from datetime import datetime, timezone
import json
import re
from pydantic import BaseModel, ValidationError

import requests
from bs4 import BeautifulSoup

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/YigitErenYil/polite-scraper)"
TIMEOUT = 10
CACHE_DIR = "cache"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
DELAY_SECONDS = 0.5
MAX_PAGES = 3

class BookRecord(BaseModel):
    title: str
    product_url: str
    price_gbp: float
    price_text: str
    availability_text: str
    rating_text: str | None
    description: str | None
    source_page: str
    fetched_at: str


def fetch_page(url: str, cache_name: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, cache_name)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT url={url} size={len(html)} bytes")
        return html

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: status {response.status_code}")

    response.encoding = "utf-8"
    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH url={url} status={response.status_code} size={len(html)} bytes")
    time.sleep(DELAY_SECONDS)
    return html



def discover_catalogue_pages(start_url: str):
    """Follow the catalogue's 'next' link starting from start_url, up to MAX_PAGES."""
    pages = []
    url = start_url
    page_number = 1

    while url and page_number <= MAX_PAGES:
        cache_name = f"catalogue-page-{page_number}.html"
        html = fetch_page(url, cache_name)
        pages.append((url, html))

        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.select_one("li.next a")
        if next_link and page_number < MAX_PAGES:
            url = urljoin(url, next_link["href"])
            page_number += 1
        else:
            url = None

    return pages


def extract_book_links(pages):
    """Given [(page_url, html), ...], return a deduplicated list of absolute book URLs."""
    links = []
    for page_url, html in pages:
        soup = BeautifulSoup(html, "html.parser")
        for article in soup.select("article.product_pod"):
            a_tag = article.select_one("h3 a")
            if a_tag and a_tag.get("href"):
                absolute_url = urljoin(page_url, a_tag["href"])
                links.append(absolute_url)

    unique_links = list(dict.fromkeys(links))  # dedupe, keep order
    return unique_links

def cache_name_for_book(book_url: str) -> str:
    # e.g. https://.../a-light-in-the-attic_1000/index.html -> a-light-in-the-attic_1000.html
    slug = book_url.rstrip("/").split("/")[-2]
    return f"book-{slug}.html"


def extract_book_record(book_url: str, source_page: str) -> dict:
    cache_name = cache_name_for_book(book_url)
    html = fetch_page(book_url, cache_name)
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("div.product_main h1").get_text(strip=True)

    price_text = soup.select_one("p.price_color").get_text(strip=True)

    availability_text = soup.select_one("p.availability").get_text(strip=True)

    rating_tag = soup.select_one("p.star-rating")
    rating_classes = rating_tag.get("class", [])
    rating_text = next((c for c in rating_classes if c != "star-rating"), None)

    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.get_text(strip=True) if description_tag else None

    return {
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

def normalize_record(raw: dict) -> dict:
    price_match = re.search(r"[\d.]+", raw["price_text"])
    price_gbp = float(price_match.group()) if price_match else None

    return {
        "title": raw["title"],
        "product_url": raw["product_url"],
        "price_gbp": price_gbp,
        "price_text": raw["price_text"],
        "availability_text": raw["availability_text"],
        "rating_text": raw["rating_text"],
        "description": raw["description"],
        "source_page": raw["source_page"],
        "fetched_at": raw["fetched_at"],
    }

if __name__ == "__main__":
    pages = discover_catalogue_pages(START_URL)
    book_links = extract_book_links(pages)

    print(f"catalogue_pages={len(pages)}")
    print(f"discovered={len(book_links)}")
    print(f"unique_urls={len(book_links)}")

    url_to_source = {}
    for page_url, html in pages:
        soup = BeautifulSoup(html, "html.parser")
        for article in soup.select("article.product_pod"):
            a_tag = article.select_one("h3 a")
            if a_tag and a_tag.get("href"):
                absolute_url = urljoin(page_url, a_tag["href"])
                url_to_source.setdefault(absolute_url, page_url)

    valid_records = {}  # keyed by product_url, so reruns don't duplicate
    invalid_records = []

    for link in book_links:
        raw = extract_book_record(link, url_to_source[link])
        normalized = normalize_record(raw)

        try:
            validated = BookRecord(**normalized)
            valid_records[validated.product_url] = validated.model_dump()
        except ValidationError as e:
            invalid_records.append({"record": normalized, "error": str(e)})

    os.makedirs("output", exist_ok=True)
    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(list(valid_records.values()), f, indent=2, ensure_ascii=False)

    with open("output/errors.json", "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)

    print(f"detail_pages={len(book_links)}")
    print(f"valid_records={len(valid_records)}")
    print(f"invalid_records={len(invalid_records)}")