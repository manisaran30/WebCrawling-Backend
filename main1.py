import json
import asyncio
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_async
import tldextract
import random

START_DOMAINS = [
    "https://www.virgio.com/",
    "https://www.tatacliq.com/",
    "https://www.nykaafashion.com/",
    "https://www.westside.com/"
]

PRODUCT_HINTS = ['product', '/p/', 'item', 'prod', '/mp000000', '/p-', 'products', 'catalog']

MAX_CONCURRENT_PAGES = 5
MAX_PAGES_PER_SITE = 100
REQUEST_TIMEOUT = 15000  # milliseconds

# Site-specific URL patterns
SITE_PATTERNS = {
    "tatacliq": {
        "product": re.compile(r"/[a-z0-9\-]+/p-[a-z0-9]+", re.I),
        "category": re.compile(r"/mens-clothing/c-msh11/page-\d+", re.I)
    },
    "westside": {
        "product": re.compile(r"/store/product/.*/prod\w+", re.I),
        "category": re.compile(r"/store/category/", re.I)
    },
    "nykaafashion": {
        "product": re.compile(r"/p/|/product/", re.I)
    }
}

def is_product_url(url, site):
    url = url.lower()
    domain = tldextract.extract(url).registered_domain
    site_key = domain.replace(".com", "").replace(".", "")
    
    # Check site-specific patterns first
    if site_key in SITE_PATTERNS:
        if SITE_PATTERNS[site_key].get("product", None) and SITE_PATTERNS[site_key]["product"].search(url):
            return True
        
        # For Westside, we need to be more aggressive in following category pages
        if site_key == "westside" and SITE_PATTERNS[site_key]["category"].search(url):
            return False  # We'll still follow these, but they're not product pages
    
    # Generic check for other platforms
    score = sum(hint in url for hint in PRODUCT_HINTS)
    if '/p-' in url or '/p/' in url:
        score += 1
    return score >= 2

async def process_url(page, url, domain, visited, queue, product_urls, site):
    try:
        await page.goto(url, timeout=REQUEST_TIMEOUT, wait_until="domcontentloaded")
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')

        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            parsed = urlparse(full_url)
            if not parsed.scheme.startswith("http"):
                continue

            ext_domain = tldextract.extract(full_url).registered_domain
            if ext_domain != domain:
                continue

            # For Westside, we need to follow category pages to find products
            site_key = domain.replace(".com", "").replace(".", "")
            if site_key == "westside" and SITE_PATTERNS[site_key]["category"].search(full_url):
                if full_url not in visited and len(visited) + len(queue) < MAX_PAGES_PER_SITE:
                    queue.append(full_url)
                continue

            if is_product_url(full_url, site):
                product_urls.add(full_url)

            if full_url not in visited and len(visited) + len(queue) < MAX_PAGES_PER_SITE:
                queue.append(full_url)

    except PlaywrightTimeoutError:
        print(f"[TIMEOUT] {url}")
    except Exception as e:
        print(f"[ERROR] Failed at {url}: {e}")


async def crawl_site(browser, start_url, site):
    visited = set()
    product_urls = set()
    queue = [start_url]
    domain = tldextract.extract(start_url).registered_domain

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        locale="en-US",
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/"
        },
        viewport={"width": 1280, "height": 800}
    )

    pages = [await context.new_page() for _ in range(min(MAX_CONCURRENT_PAGES, MAX_PAGES_PER_SITE))]
    for page in pages:
        await stealth_async(page)

    async def worker():
        while queue and len(visited) < MAX_PAGES_PER_SITE:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            page = random.choice(pages)
            print(f"➡ Visiting: {url}")
            await process_url(page, url, domain, visited, queue, product_urls, site)

    workers = [asyncio.create_task(worker()) for _ in range(len(pages))]
    await asyncio.gather(*workers)
    await context.close()
    return list(product_urls)


async def main():
    results = {url: [] for url in START_DOMAINS}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        for site in START_DOMAINS:
            print(f"\n🔍 Crawling {site}")
            try:
                site_name = tldextract.extract(site).domain
                product_links = await crawl_site(browser, site, site_name)
                results[site] = product_links
                print(f"✅ Found {len(product_links)} products from {site}")
            except Exception as e:
                print(f"[FATAL] Error while crawling {site}: {e}")

        await browser.close()

    with open("product_urls1.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        print("\n💾 Saved product URLs to product_urls1.json")


if __name__ == "__main__":
    asyncio.run(main())