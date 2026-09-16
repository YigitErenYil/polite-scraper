import os
import time
import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/YigitErenYil/polite-scraper)"
TIMEOUT = 10
CACHE_DIR = "cache"
BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"


def fetch_page(page_number: int) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"catalogue-page-{page_number}.html")

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT page={page_number} size={len(html)} bytes")
        return html

    url = BASE_URL.format(page_number)
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: status {response.status_code}")

    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH page={page_number} status={response.status_code} size={len(html)} bytes")
    return html


if __name__ == "__main__":
    fetch_page(1)