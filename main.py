import asyncio
import json
import nest_asyncio
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

nest_asyncio.apply()

URLS = {
    "https://www.virgio.com/": ["https://www.virgio.com/"],
    "https://www.tatacliq.com/": [
        "https://www.tatacliq.com/mens-clothing/c-msh11/page-1?q=%3Arelevance%3Acategory%3AMSH11%3AinStockFlag%3Atrue",
        "https://www.tatacliq.com/search?text=Ethnic%20Wear%20-%20Shop%20all%20:relevance:list:listId_ea75fe58ecdf4058898f36e03c8ab3d3&icid2=catd:nav:regu:wnav:m1311:mulb:bst:01:R1",
        "https://www.tatacliq.com/kids/c-msh21/page-1?q=%3Arelevance%3Acategory%3AMSH21%3AinStockFlag%3Atrue&icid2=catd:nav:regu:knav:m21:mulb:bst:01:R1"
    ],
    "https://www.nykaafashion.com/": ["https://www.nykaafashion.com/women/westernwear/c/3"],
    "https://www.westside.com/": [
        "https://www.westside.com/collections/women",
        "https://www.westside.com/collections/men",
        "https://www.westside.com/collections/kids",
        "https://www.westside.com/collections/home-kitchen-serve-ware"
    ]
}

PRODUCT_URL_PATTERNS = {
    "tatacliq.com": lambda href: re.search(r"/[a-z0-9\-]+/p-mp\d+", href or ""),
    "nykaafashion.com": lambda href: re.search(r"/[a-z0-9\-]+/p/\d+", href or ""),
    "virgio.com": lambda href: re.search(r"/products/[^/]+$", href or ""),
    "westside.com": lambda href: re.search(r"/products/[^/?]+(\?.*)?$", href or "")
}

def get_domain_pattern(url):
    domain = urlparse(url).netloc
    for known_domain, pattern in PRODUCT_URL_PATTERNS.items():
        if known_domain in domain:
            return pattern
    return None

async def fetch_product_urls(context, url):
    try:
        page = await context.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state('networkidle')

        for _ in range(8):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(2)

        print(f"✅ Loaded: {url}")
        html = await page.content()
        await page.close()

        soup = BeautifulSoup(html, "html.parser")
        anchors = soup.find_all("a")

        pattern = get_domain_pattern(url)
        product_urls = set()

        for a in anchors:
            href = a.get("href")
            if href and pattern and pattern(href):
                full_url = href if href.startswith("http") else urljoin(url, href)
                product_urls.add(full_url)

        return list(product_urls)

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return []

async def retry_fetch_product_urls(context, url, retries=2):
    for attempt in range(retries):
        links = await fetch_product_urls(context, url)
        if links:
            return links
        print(f"🔁 Retry {attempt + 1} for {url}")
    return []

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        result = {}

        for base_url, category_urls in URLS.items():
            print(f"\n🔍 Scraping: {base_url}")
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            all_links = []

            for category in category_urls:
                links = await retry_fetch_product_urls(context, category)
                print(f"🔗 {len(links)} links from {category}")
                all_links.extend(links)

            await context.close()
            result[base_url] = list(set(all_links))  # Deduplicate

        await browser.close()

        with open("product_urls.json", "w") as f:
            json.dump(result, f, indent=2)

        print("\n✅ Saved to product_urls.json")

if __name__ == "__main__":
    asyncio.run(main())
