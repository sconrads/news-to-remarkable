# fetcher/article.py - Henter full artikkeltekst via autentisert Playwright-session

import logging
import os
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BROWSERS_PATH = os.getenv("PLAYWRIGHT_BROWSERS_PATH", str(Path(__file__).parent.parent / "browsers"))

logger = logging.getLogger(__name__)

# CSS-selektorer for artikkeltekst per avis
ARTICLE_SELECTORS = {
    "vg": [
        "div.article-body",
        "div[class*='article-body']",
        "article",
    ],
    "aftenposten": [
        "div.article-body",
        "div[class*='article-body']",
        "section[class*='article']",
        "article",
    ],
    "e24": [
        "div.article-body",
        "div[class*='article-body']",
        "article",
    ],
    "morgenbladet": [
        "div.article-body",
        "div[class*='article-body']",
        "div[class*='ArticleBody']",
        "section[class*='article']",
        "article",
    ],
}

# Elementer vi vil fjerne fra artikkelteksten
REMOVE_SELECTORS = [
    "figure", "img", "video", "aside", "nav",
    "div[class*='ad']", "div[class*='banner']",
    "div[class*='related']", "div[class*='newsletter']",
    "div[class*='paywall']", "div[class*='subscribe']",
    "button", "form", "script", "style",
]


def _detect_source(url: str) -> str:
    if "vg.no" in url:
        return "vg"
    if "aftenposten.no" in url:
        return "aftenposten"
    if "e24.no" in url:
        return "e24"
    if "morgenbladet.no" in url:
        return "morgenbladet"
    return "vg"


def _extract_text(html: str, source: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Fjern uønskede elementer
    for sel in REMOVE_SELECTORS:
        for el in soup.select(sel):
            el.decompose()

    # Finn artikkeltekst
    selectors = ARTICLE_SELECTORS.get(source, ["article"])
    for sel in selectors:
        container = soup.select_one(sel)
        if container:
            paragraphs = container.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    # Fallback: alle <p>-tagger på siden
    paragraphs = soup.find_all("p")
    return "\n\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)


def fetch_articles_text(
    urls_with_sources: list,
    schibsted_cookies: list,
    morgenbladet_cookies: Optional[list] = None,
) -> dict:
    """
    Henter artikkeltekst for en liste med (url, source)-tupler.
    Injiserer riktige cookies per avis (Schibsted for vg/aftenposten/e24,
    Piano for morgenbladet).
    Returnerer dict: url -> tekst
    """
    results = {}
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = BROWSERS_PATH

    # Grupper URLs etter cookie-sett: Schibsted vs. Morgenbladet
    schibsted_sources = {"vg", "aftenposten", "e24"}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        def make_context(cookies):
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                )
            )
            if cookies:
                ctx.add_cookies(cookies)
            return ctx

        schibsted_ctx = make_context(schibsted_cookies)
        morgenbladet_ctx = make_context(morgenbladet_cookies or [])

        schibsted_page = schibsted_ctx.new_page()
        morgenbladet_page = morgenbladet_ctx.new_page()

        for url, source in urls_with_sources:
            page = morgenbladet_page if source == "morgenbladet" else schibsted_page
            try:
                logger.info(f"  Henter artikkel: {url[:80]}...")
                page.goto(url, timeout=25000, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except PlaywrightTimeoutError:
                    pass
                html = page.content()
                text = _extract_text(html, source)
                results[url] = text
                logger.debug(f"    {len(text)} tegn hentet")
            except PlaywrightTimeoutError:
                logger.warning(f"  Timeout for {url}")
                results[url] = ""
            except Exception as e:
                logger.warning(f"  Feil for {url}: {e}")
                results[url] = ""

        browser.close()

    return results
