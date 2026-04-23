"""Prospect Scraper — Find SA e-commerce stores using Playwright.

Generates qualified leads for StudEx AI customer service automation.
Scrapes Google, Facebook, Instagram for e-commerce businesses.
"""

import os
import csv
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from playwright.async_api import async_playwright

SAST = timezone(timedelta(hours=2))

# Output directory for scraped leads
OUTPUT_DIR = Path(__file__).parent.parent / "leads"
OUTPUT_DIR.mkdir(exist_ok=True)


class ProspectScraper:
    """Scrape e-commerce prospects from multiple sources."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.leads: List[Dict] = []

    async def scrape_google_search(
        self,
        query: str,
        location: str = "South Africa",
        limit: int = 50
    ) -> List[Dict]:
        """Scrape Google search results for e-commerce stores.

        Args:
            query: Search query (e.g., "online store", "boutique")
            location: Geographic filter
            limit: Max results to extract

        Returns:
            List of prospect dicts
        """
        prospects = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()

            # Google search with location
            search_url = f"https://www.google.co.za/search?q={query}+{location}+online+store&num={limit}"
            await page.goto(search_url, wait_until="networkidle")

            # Wait for results
            await page.wait_for_selector(".g", timeout=10000)

            # Extract results
            results = await page.query_selector_all(".g")

            for i, result in enumerate(results[:limit]):
                try:
                    title_el = await result.query_selector("h3")
                    title = await title_el.inner_text() if title_el else ""

                    link_el = await result.query_selector("a")
                    url = await link_el.get_attribute("href") if link_el else ""

                    # Skip Google-owned URLs
                    if any(x in url for x in ["google.", "youtube.", "facebook.com"]):
                        continue

                    # Extract snippet/description
                    snippet_el = await result.query_selector(".VwiC3b")
                    snippet = await snippet_el.inner_text() if snippet_el else ""

                    prospects.append({
                        "source": "google",
                        "name": title,
                        "url": url,
                        "description": snippet,
                        "query": query,
                        "scraped_at": datetime.now(SAST).isoformat(),
                    })
                except Exception:
                    continue

            await browser.close()

        return prospects

    async def extract_contact_info(self, url: str) -> Dict:
        """Visit a website and extract contact information.

        Args:
            url: Website URL

        Returns:
            Dict with email, phone, whatsapp, social links
        """
        contact = {
            "url": url,
            "email": None,
            "phone": None,
            "whatsapp": False,
            "facebook": None,
            "instagram": None,
            "tiktok": None,
        }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()
                page = await context.new_page()

                # Try main site
                await page.goto(url, wait_until="networkidle", timeout=15000)

                # Look for contact page
                contact_links = await page.query_selector_all("a[href*='contact'], a[href*='Contact']")
                if contact_links:
                    for link in contact_links[:3]:
                        href = await link.get_attribute("href")
                        if href and not href.startswith("#"):
                            try:
                                await page.goto(href, wait_until="networkidle", timeout=10000)
                                break
                            except:
                                continue

                # Extract emails from page
                emails = await page.evaluate("""() => {
                    const text = document.body.innerText;
                    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g;
                    return [...new Set(text.match(emailRegex) || [])];
                }""")
                contact["email"] = emails[0] if emails else None

                # Look for WhatsApp click-to-chat
                whatsapp = await page.query_selector("a[href*='wa.me'], a[href*='whatsapp.com']")
                contact["whatsapp"] = whatsapp is not None

                # Social links
                social_selectors = {
                    "facebook": "a[href*='facebook.com']",
                    "instagram": "a[href*='instagram.com']",
                    "tiktok": "a[href*='tiktok.com']",
                }

                for platform, selector in social_selectors.items():
                    el = await page.query_selector(selector)
                    if el:
                        contact[platform] = await el.get_attribute("href")

                await browser.close()

        except Exception as e:
            contact["error"] = str(e)

        return contact

    async def scrape_ecommerce_platform(
        self,
        platform: str,
        location: str = "South Africa",
        limit: int = 50
    ) -> List[Dict]:
        """Scrape stores from specific e-commerce platforms.

        Args:
            platform: "shopify", "woocommerce", "yoco"
            location: Geographic filter
            limit: Max results

        Returns:
            List of prospect dicts
        """
        prospects = []

        # Platform-specific search URLs
        platform_urls = {
            "shopify": f"https://www.google.co.za/search?q=site:myshopify.com+{location}",
            "woocommerce": f"https://www.google.co.za/search?q=powered+by+woocommerce+{location}+store",
            "yoco": f"https://www.google.co.za/search?q=pay+with+yoco+{location}+store",
        }

        search_url = platform_urls.get(platform)
        if not search_url:
            return prospects

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(search_url, wait_until="networkidle")
            await page.wait_for_selector(".g", timeout=10000)

            results = await page.query_selector_all(".g")

            for result in results[:limit]:
                try:
                    title_el = await result.query_selector("h3")
                    title = await title_el.inner_text() if title_el else ""

                    link_el = await result.query_selector("a")
                    url = await link_el.get_attribute("href") if link_el else ""

                    if any(x in url for x in ["google.", "facebook."]):
                        continue

                    prospects.append({
                        "source": f"platform:{platform}",
                        "name": title,
                        "url": url,
                        "platform": platform,
                        "location": location,
                        "scraped_at": datetime.now(SAST).isoformat(),
                    })
                except:
                    continue

            await browser.close()

        return prospects

    async def enrich_lead(self, lead: Dict) -> Dict:
        """Enrich a lead with contact info and qualification data.

        Args:
            lead: Basic lead dict with URL

        Returns:
            Enriched lead dict
        """
        url = lead.get("url", "")
        if not url:
            return lead

        # Get contact info
        contact = await self.extract_contact_info(url)

        # Merge
        enriched = {**lead, **contact}

        # Qualification score
        score = 0
        if contact.get("email"):
            score += 1
        if contact.get("whatsapp"):
            score += 2  # WhatsApp = ready for our product
        if contact.get("facebook") or contact.get("instagram"):
            score += 1
        if any(platform in url for platform in ["shopify", "woocommerce", "yoco"]):
            score += 2  # E-commerce platform = qualified

        enriched["qualification_score"] = score
        enriched["qualified"] = score >= 3

        return enriched

    async def scrape_batch(
        self,
        queries: List[str],
        location: str = "South Africa",
        limit_per_query: int = 20
    ) -> List[Dict]:
        """Scrape multiple queries and combine results.

        Args:
            queries: List of search queries
            location: Geographic filter
            limit_per_query: Results per query

        Returns:
            Combined list of prospects
        """
        all_prospects = []

        for query in queries:
            print(f"Scraping: {query}")
            prospects = await self.scrape_google_search(query, location, limit_per_query)
            all_prospects.extend(prospects)
            print(f"  Found {len(prospects)} prospects")

        # Remove duplicates by URL
        seen = set()
        unique = []
        for p in all_prospects:
            if p.get("url") not in seen:
                seen.add(p["url"])
                unique.append(p)

        return unique

    def save_to_csv(self, leads: List[Dict], filename: Optional[str] = None):
        """Save leads to CSV file.

        Args:
            leads: List of lead dicts
            filename: Output filename (default: auto-generated)
        """
        if not filename:
            timestamp = datetime.now(SAST).strftime("%Y%m%d_%H%M%S")
            filename = f"prospects_{timestamp}.csv"

        filepath = OUTPUT_DIR / filename

        if not leads:
            print("No leads to save")
            return

        # Get all keys
        keys = set()
        for lead in leads:
            keys.update(lead.keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(leads)

        print(f"Saved {len(leads)} leads to {filepath}")
        return filepath

    def save_to_json(self, leads: List[Dict], filename: Optional[str] = None):
        """Save leads to JSON file."""
        if not filename:
            timestamp = datetime.now(SAST).strftime("%Y%m%d_%H%M%S")
            filename = f"prospects_{timestamp}.json"

        filepath = OUTPUT_DIR / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, default=str)

        print(f"Saved {len(leads)} leads to {filepath}")
        return filepath


# Pre-defined search queries for SA e-commerce
SA_ECOMMERCE_QUERIES = [
    "online store",
    "boutique",
    "fashion store",
    "homeware",
    "beauty products",
    "fitness supplements",
    "pet supplies",
    "baby products",
    "jewelry",
    "electronics",
    "organic food",
    "sportswear",
    "furniture",
    "cosmetics",
    "shoes",
]


async def main():
    """Run prospect scraping."""
    scraper = ProspectScraper(headless=True)

    # Scrape top queries
    queries = SA_ECOMMERCE_QUERIES[:5]  # Start with 5
    prospects = await scraper.scrape_batch(queries, limit_per_query=20)

    print(f"\nTotal prospects found: {len(prospects)}")

    # Save results
    scraper.save_to_csv(prospects)
    scraper.save_to_json(prospects)

    # Enrich top 10 (slow, do selectively)
    print("\nEnriching top 10 prospects...")
    enriched = []
    for p in prospects[:10]:
        enriched_lead = await scraper.enrich_lead(p)
        enriched.append(enriched_lead)
        print(f"  {enriched_lead.get('name', 'Unknown')}: Score {enriched_lead.get('qualification_score', 0)}")

    # Save enriched
    scraper.save_to_csv(enriched, "prospects_enriched.csv")

    # Summary
    qualified = [e for e in enriched if e.get("qualified")]
    print(f"\nQualified leads: {len(qualified)}/{len(enriched)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
