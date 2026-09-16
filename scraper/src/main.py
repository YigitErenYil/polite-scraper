import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/YigitErenYil/polite-scraper)"
TIMEOUT = 10
CACHE_DIR = "cache"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
DELAY_SECONDS = 0.5
MAX_PAGES = 3


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


if __name__ == "__main__":
    pages = discover_catalogue_pages(START_URL)
    book_links = extract_book_links(pages)

    print(f"catalogue_pages={len(pages)}")
    print(f"discovered={len(book_links)}")
    print(f"unique_urls={len(book_links)}")