"""
Playwright Service — Browser automation for scraping, screenshots, and testing.
Headless Chromium for pages that need JS rendering.
"""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page


class PlaywrightService:
    def __init__(self):
        self._browser: Optional[Browser] = None

    async def _get_browser(self) -> Browser:
        if not self._browser or not self._browser.is_connected():
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(headless=True)
        return self._browser

    async def screenshot(self, url: str, full_page: bool = True) -> dict:
        """Take a screenshot of a URL — useful for competitor visual analysis."""
        try:
            browser = await self._get_browser()
            page = await browser.new_page(viewport={"width": 1440, "height": 900})
            await page.goto(url, wait_until="networkidle", timeout=30000)
            path = f"/tmp/screenshot_{hash(url) % 100000}.png"
            await page.screenshot(path=path, full_page=full_page)
            await page.close()
            return {"url": url, "screenshot_path": path, "status": "captured"}
        except Exception as e:
            return {"url": url, "error": str(e)}

    async def scrape_rendered(self, url: str, selector: Optional[str] = None) -> dict:
        """Scrape a JS-rendered page — gets content after JavaScript execution."""
        try:
            browser = await self._get_browser()
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)

            if selector:
                elements = await page.query_selector_all(selector)
                texts = [await el.inner_text() for el in elements]
                await page.close()
                return {"url": url, "selector": selector, "count": len(texts), "texts": texts}

            title = await page.title()
            content = await page.inner_text("body")
            links = await page.eval_on_selector_all("a[href]", "els => els.map(e => ({text: e.innerText.trim(), href: e.href})).filter(l => l.text)")
            await page.close()
            return {
                "url": url,
                "title": title,
                "content_length": len(content),
                "content_preview": content[:2000],
                "links_found": len(links),
            }
        except Exception as e:
            return {"url": url, "error": str(e)}

    async def extract_prices(self, url: str) -> dict:
        """Extract pricing from a competitor page — Studex Meat competitive intel."""
        try:
            browser = await self._get_browser()
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Extract anything that looks like a price (ZAR)
            prices = await page.evaluate("""() => {
                const priceRegex = /R\\s?[\\d,]+\\.?\\d{0,2}|\\d+[.,]\\d{2}\\s*(?:ZAR|rand)/gi;
                const text = document.body.innerText;
                const matches = text.match(priceRegex) || [];
                return [...new Set(matches)].slice(0, 50);
            }""")

            await page.close()
            return {"url": url, "prices_found": len(prices), "prices": prices}
        except Exception as e:
            return {"url": url, "error": str(e)}

    async def monitor_social(self, url: str) -> dict:
        """Grab social media metrics from a public page."""
        try:
            browser = await self._get_browser()
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)

            meta_tags = await page.evaluate("""() => {
                const metas = {};
                document.querySelectorAll('meta[property], meta[name]').forEach(m => {
                    const key = m.getAttribute('property') || m.getAttribute('name');
                    metas[key] = m.getAttribute('content');
                });
                return metas;
            }""")

            title = await page.title()
            await page.close()
            return {"url": url, "title": title, "meta": meta_tags}
        except Exception as e:
            return {"url": url, "error": str(e)}

    async def close(self):
        if self._browser and self._browser.is_connected():
            await self._browser.close()
