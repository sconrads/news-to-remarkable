#!/usr/bin/env python3
# main.py - Koordinerer hele nyhets-til-reMarkable-flyten

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Legg til prosjektmappen i Python-path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def _filter_and_trim(categorized: dict, texts: dict) -> dict:
    """
    Filtrerer bort korte artikler og beholder maks MAX_ARTICLES_PER_CATEGORY
    per kategori. Sorterer artikler etter tekstlengde (lengst først).
    """
    from config import MAX_ARTICLES_PER_CATEGORY, MIN_ARTICLE_WORDS

    result = {}
    for cat, articles in categorized.items():
        # Fyll inn tekst og tell ord
        qualified = []
        for a in articles:
            a.full_text = texts.get(a.url, "")
            word_count = len(a.full_text.split()) if a.full_text else 0
            if word_count >= MIN_ARTICLE_WORDS:
                qualified.append((word_count, a))
            else:
                logger.info(
                    f"  [{cat}] Forkastet kort artikkel ({word_count} ord): {a.title[:60]}"
                )

        # Sorter etter lengde, lengste først — gir de mest substansielle artiklene
        qualified.sort(key=lambda x: x[0], reverse=True)
        result[cat] = [a for _, a in qualified[:MAX_ARTICLES_PER_CATEGORY]]
        logger.info(
            f"  [{cat}] {len(result[cat])} artikler etter kvalitetsfiltrering "
            f"(av {len(articles)} kandidater)"
        )

    return result


def main():
    logger.info("=== Starter nyhetsinnhenting ===")

    # --- 1. Les credentials ---
    email = os.getenv("SCHIBSTED_EMAIL")
    password = os.getenv("SCHIBSTED_PASSWORD")
    if not email or not password:
        logger.error("SCHIBSTED_EMAIL og SCHIBSTED_PASSWORD må settes i .env")
        sys.exit(1)

    # --- 2. Autentiser mot Schibsted ---
    from fetcher.auth import get_authenticated_cookies
    logger.info("Henter Schibsted-cookies ...")
    schibsted_cookies = get_authenticated_cookies(email, password)

    # --- 2b. Autentiser mot Morgenbladet hvis aktivert ---
    from config import ENABLED_SOURCES
    morgenbladet_cookies = []
    if "morgenbladet" in ENABLED_SOURCES:
        mb_email = os.getenv("MORGENBLADET_EMAIL") or email
        mb_password = os.getenv("MORGENBLADET_PASSWORD") or password
        if mb_email and mb_password:
            from fetcher.auth import get_morgenbladet_cookies
            logger.info("Henter Morgenbladet-cookies ...")
            morgenbladet_cookies = get_morgenbladet_cookies(mb_email, mb_password)
        else:
            logger.warning("Morgenbladet er aktivert men mangler credentials — henter kun RSS-sammendrag.")

    # --- 3. Hent RSS-feeds ---
    from fetcher.rss import fetch_all_feeds, fetch_feed
    logger.info("Henter RSS-feeds ...")
    articles = fetch_all_feeds()
    logger.info(f"Totalt {len(articles)} artikler fra RSS")

    # --- 3b. Hent siste nyheter fra Aftenposten til forsiden ---
    from config import MAX_BREAKING_HEADLINES
    breaking_headlines = []
    if "aftenposten" in ENABLED_SOURCES:
        all_aftenposten = fetch_feed("aftenposten")
        # Sorter etter publiseringstidspunkt, nyeste først
        all_aftenposten.sort(
            key=lambda a: a.published if a.published else __import__("datetime").datetime.min,
            reverse=True,
        )
        breaking_headlines = all_aftenposten[:MAX_BREAKING_HEADLINES]
        logger.info(f"  {len(breaking_headlines)} siste nyheter hentet til forsiden")

    # --- 3c. Hent kalender-hendelser for i dag ---
    from fetcher.calendar import fetch_todays_events
    logger.info("Henter kalender-hendelser ...")
    calendar_events = fetch_todays_events()

    # --- 4. Kategoriser ---
    from categorizer import categorize
    logger.info("Kategoriserer artikler ...")
    categorized = categorize(articles)

    # --- 5. Hent full artikkeltekst for alle kandidater ---
    from fetcher.article import fetch_articles_text
    logger.info("Henter full artikkeltekst ...")

    url_source_pairs = []
    for arts in categorized.values():
        for a in arts:
            url_source_pairs.append((a.url, a.source))

    texts = fetch_articles_text(url_source_pairs, schibsted_cookies, morgenbladet_cookies)

    # --- 6. Filtrer bort korte artikler og begrens til 3 per kategori ---
    logger.info("Filtrerer artikler etter kvalitet ...")
    categorized = _filter_and_trim(categorized, texts)

    total = sum(len(v) for v in categorized.values())
    logger.info(f"Totalt {total} artikler etter kvalitetsfiltrering")

    if total == 0:
        logger.warning("Ingen artikler funnet etter filtrering - avslutter")
        sys.exit(0)

    # --- 7. Render PDF ---
    from renderer import render_pdf
    logger.info("Genererer PDF ...")
    pdf_path = render_pdf(categorized, breaking_headlines=breaking_headlines, calendar_events=calendar_events)

    # --- 8. Rydd opp gamle PDFer på reMarkable (eldre enn 5 dager) ---
    from sender import cleanup_old_pdfs
    logger.info("Rydder opp gamle PDFer på reMarkable ...")
    cleanup_old_pdfs()

    # --- 9. Send til reMarkable ---
    from sender import upload_to_remarkable
    logger.info("Sender til reMarkable ...")
    success = upload_to_remarkable(pdf_path)

    if success:
        logger.info("=== Ferdig! PDF sendt til reMarkable. ===")
    else:
        logger.error("=== PDF generert, men opplasting til reMarkable feilet. ===")
        logger.info(f"PDF ligger lokalt: {pdf_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
