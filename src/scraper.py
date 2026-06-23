"""
scraper.py  (v4 — Selenium headless browser)
─────────────────────────────────────────────
Uses a real headless Chrome browser via Selenium to bypass
Shopify's Cloudflare bot protection (which blocks requests/urllib).

Usage:
    python src/scraper.py
"""

import os
import re
import time
import json
from pathlib import Path
from tqdm import tqdm

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://help.shopify.com"

# ── All article URLs to scrape ─────────────────────────────────────────
ARTICLE_URLS = {
    "intro": [
        "/en/manual/intro-to-shopify/overview",
        "/en/manual/intro-to-shopify/pricing-plans",
        "/en/manual/intro-to-shopify/initial-setup",
        "/en/manual/intro-to-shopify/hiring-help",
        "/en/manual/intro-to-shopify/store-design",
        "/en/manual/migrating-to-shopify",
    ],
    "products": [
        "/en/manual/products",
        "/en/manual/products/add-update-products",
        "/en/manual/products/variants",
        "/en/manual/products/inventory",
        "/en/manual/products/collections",
        "/en/manual/products/import-export/import-products",
        "/en/manual/products/import-export/export-products",
        "/en/manual/products/product-media",
    ],
    "inventory": [
        "/en/manual/products/inventory",
        "/en/manual/products/inventory/managing-inventory",
        "/en/manual/products/inventory/transfers",
    ],
    "orders": [
        "/en/manual/orders",
        "/en/manual/orders/manage-orders",
        "/en/manual/orders/fulfillment",
        "/en/manual/orders/refunds",
        "/en/manual/orders/cancellations",
        "/en/manual/orders/notifications",
        "/en/manual/orders/create-orders",
    ],
    "payments": [
        "/en/manual/payments",
        "/en/manual/payments/shopify-payments",
        "/en/manual/payments/third-party-providers",
        "/en/manual/payments/paypal",
        "/en/manual/taxes",
        "/en/manual/taxes/setting-up",
        "/en/manual/payments/accelerated-checkouts",
        "/en/manual/checkout-settings",
        "/en/manual/checkout-settings/checkout-customization",
    ],
    "shipping": [
        "/en/manual/shipping",
        "/en/manual/shipping/setting-up-and-managing-your-shipping/shipping-profiles",
        "/en/manual/shipping/setting-up-and-managing-your-shipping/rates-and-methods",
        "/en/manual/shipping/local-delivery",
        "/en/manual/shipping/shopify-shipping",
        "/en/manual/shipping/understanding-shipping",
    ],
    "marketing": [
        "/en/manual/promoting-marketing",
        "/en/manual/promoting-marketing/seo/seo-overview",
        "/en/manual/promoting-marketing/discount-codes",
        "/en/manual/promoting-marketing/email-marketing",
        "/en/manual/promoting-marketing/campaigns",
        "/en/manual/promoting-marketing/automations",
    ],
    "discounts": [
        "/en/manual/discounts",
        "/en/manual/discounts/discount-types",
        "/en/manual/discounts/create-discount-codes",
    ],
    "online-store": [
        "/en/manual/online-store/themes",
        "/en/manual/online-store/themes/customizing-themes",
        "/en/manual/online-store/pages",
        "/en/manual/online-store/blogs",
        "/en/manual/online-store/navigation",
        "/en/manual/domains/add-a-domain",
    ],
    "customers": [
        "/en/manual/customers",
        "/en/manual/customers/manage-customers",
        "/en/manual/customers/customer-accounts",
        "/en/manual/customers/customer-segmentation",
        "/en/manual/customers/tags",
    ],
    "analytics": [
        "/en/manual/reports-and-analytics",
        "/en/manual/reports-and-analytics/shopify-reports",
        "/en/manual/reports-and-analytics/live-view",
        "/en/manual/reports-and-analytics/analytics-overview",
        "/en/manual/reports-and-analytics/reports/report-types",
        "/en/manual/reports-and-analytics/reports/finances-reports",
    ],
    "apps": [
        "/en/manual/apps",
        "/en/manual/apps/working-with-apps",
        "/en/manual/apps/app-types",
        "/en/manual/apps/managing-apps",
    ],
}


# ── Browser setup ─────────────────────────────────────────────────────────

def create_driver():
    """Create a headless Chrome driver that looks like a real browser."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    # Selenium 4.6+ manages chromedriver automatically — no webdriver_manager needed
    driver = webdriver.Chrome(options=options)

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ── Article scraping ──────────────────────────────────────────────────────

def scrape_article(driver, url: str, section: str) -> dict | None:
    """Load a page and extract article content."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        driver.get(url)

        # Wait for main content to load (max 10 sec)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        # Small extra wait for JS-rendered content
        time.sleep(1.5)

        # Check for Cloudflare challenge page
        if "Just a moment" in driver.title or "Checking your browser" in driver.page_source:
            print(f"  [CF] Cloudflare challenge on {url} — waiting 8s")
            time.sleep(8)

        # Get title
        try:
            title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            title = "Untitled"

        # Get main content
        content_blocks = []

        # Try article tag first, then main, then body
        for selector in ["article", "main", "[class*='content']", "body"]:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    container = elements[0]
                    # Tag to markdown heading prefix map
                    TAG_PREFIX = {
                        "h1": "# ",
                        "h2": "## ",
                        "h3": "### ",
                        "h4": "#### ",
                        "p":  "",
                        "li": "",
                        "td": "",
                    }

                    # Extract all text elements preserving heading structure
                    for tag in ["h1", "h2", "h3", "h4", "p", "li", "td"]:
                        nodes = container.find_elements(By.TAG_NAME, tag)
                        for node in nodes:
                            text = node.text.strip()
                            if text and len(text) > 20:
                                prefix = TAG_PREFIX.get(tag, "")
                                content_blocks.append(prefix + text)
                    if content_blocks:
                        break
            except:
                continue

        content = "\n\n".join(content_blocks)

        if len(content) < 200:
            print(f"  [SKIP] Too little content: {url}")
            return None

        return {
            "url":     url,
            "title":   title,
            "section": section,
            "content": content,
        }

    except Exception as e:
        print(f"  [ERROR] {e} → {url}")
        return None


def safe_filename(url: str) -> str:
    slug = url.replace(BASE_URL, "").replace("/en/manual/", "").replace("/", "_")
    return f"{slug[:100]}.txt"


def save_article(article: dict) -> Path:
    section_dir = RAW_DIR / article["section"]
    section_dir.mkdir(parents=True, exist_ok=True)
    filepath = section_dir / safe_filename(article["url"])
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {article['title']}\n")
        f.write(f"URL: {article['url']}\n")
        f.write(f"SECTION: {article['section']}\n")
        f.write("---\n\n")
        f.write(article["content"])
    return filepath


# ── Main ──────────────────────────────────────────────────────────────────

def scrape_all():
    print("Starting Chrome headless browser...")
    driver = create_driver()
    print("✓ Browser ready\n")

    manifest    = []
    total_saved = 0

    try:
        for section, paths in ARTICLE_URLS.items():
            print(f"\n{'='*60}")
            print(f"Section: {section.upper()}  ({len(paths)} URLs)")
            print(f"{'='*60}")
            saved = 0

            for path in tqdm(paths, desc=f"  {section}"):
                url     = BASE_URL + path
                article = scrape_article(driver, url, section)

                if article:
                    fp = save_article(article)
                    manifest.append({
                        "section":  section,
                        "title":    article["title"],
                        "url":      article["url"],
                        "filepath": str(fp),
                    })
                    saved += 1
                    print(f"  ✓ {article['title'][:60]}")

                # Polite delay between requests
                time.sleep(2)

            print(f"  → Saved {saved}/{len(paths)} articles")
            total_saved += saved

    finally:
        driver.quit()
        print("\nBrowser closed.")

    # Save manifest
    manifest_path = RAW_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ SCRAPING COMPLETE")
    print(f"   Total articles saved : {total_saved}")
    print(f"   Saved to             : {RAW_DIR.resolve()}")
    print(f"{'='*60}")
    return manifest


if __name__ == "__main__":
    scrape_all()
