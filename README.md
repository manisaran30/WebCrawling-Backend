# 🛍️ Fashion E-Commerce Product URL Scraper

This project is a Python-based web scraper that collects product page URLs from top Indian fashion e-commerce websites. It uses **Playwright** for dynamic page rendering and **BeautifulSoup** for HTML parsing.

---

## 🚀 Features

- ✅ Scrapes product URLs from:
  - [Virgio](https://www.virgio.com/)
  - [TataCliq](https://www.tatacliq.com/)
  - [Nykaa Fashion](https://www.nykaafashion.com/)
  - [Westside](https://www.westside.com/)
- ✅ Automatically scrolls and loads all product listings
- ✅ Uses pattern matching to identify valid product links
- ✅ Deduplicates and stores results in `product_urls.json`
- ✅ Built with asynchronous execution for better performance

---

## 🛠️ Tech Stack

- [Python 3.8+](https://www.python.org/)
- [Playwright](https://playwright.dev/python/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [nest_asyncio](https://pypi.org/project/nest-asyncio/)

---

## 📦 Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/your-username/fashion-url-scraper.git
   cd fashion-url-scraper
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

   Your `requirements.txt` should include:
   ```
   playwright
   beautifulsoup4
   nest_asyncio
   ```

---

## ▶️ How to Run

Run the scraper script using:

```bash
python scraper.py
```

The script will:
- Scroll through product category pages
- Extract product page URLs
- Save them into a file called `product_urls.json`

---

## 📁 Output Format

The results will be saved as a JSON file:

```json
{
  "https://www.virgio.com/": [
    "https://www.virgio.com/products/summer-floral-top",
    ...
  ],
  "https://www.tatacliq.com/": [
    "https://www.tatacliq.com/levis-blue-jeans/p-mp000000123456789",
    ...
  ]
}
```

---

## 📌 Notes

- Ensure a stable internet connection during execution.
- Run in a clean terminal (VS Code terminal or standalone) to avoid event loop conflicts.
- You can adjust scroll count and sleep delays if some product pages are missed.

---
