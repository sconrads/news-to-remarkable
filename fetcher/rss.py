# fetcher/rss.py - Henter og parser RSS-feeds fra alle aktiverte aviser

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import feedparser

from config import RSS_FEEDS, MAX_ARTICLES_PER_SOURCE, ENABLED_SOURCES

logger = logging.getLogger(__name__)


@dataclass
class RSSArticle:
    title: str
    url: str
    summary: str
    published: Optional[datetime]
    source: str          # "vg", "aftenposten", "e24", "morgenbladet"
    raw_category: str    # Avisens egen kategori-tag eller URL-sti
    full_text: str = ""  # Fylles inn av article.py


def _parse_published(entry) -> Optional[datetime]:
    try:
        return datetime(*entry.published_parsed[:6])
    except Exception:
        return None


def _extract_vg_category(entry) -> str:
    tags = getattr(entry, "tags", [])
    if tags:
        return tags[0].get("term", "")
    # Fallback: prøv å utlede fra URL-sti
    path = urlparse(entry.link).path
    parts = [p for p in path.split("/") if p]
    return parts[0] if parts else ""


def _extract_aftenposten_category(entry) -> str:
    """Aftenposten har ikke <category> i RSS - bruker URL-sti."""
    path = urlparse(entry.link).path  # f.eks. /sport/i/abc123/...
    parts = [p for p in path.split("/") if p]
    # Første segment er seksjonen (sport, norge, verden, etc.)
    return f"/{parts[0]}/" if parts else "/"


def _extract_e24_category(entry) -> str:
    tags = getattr(entry, "tags", [])
    if tags:
        return tags[0].get("term", "")
    path = urlparse(entry.link).path
    parts = [p for p in path.split("/") if p]
    return parts[0] if parts else ""


def _extract_morgenbladet_category(entry) -> str:
    """Morgenbladet bruker URL-sti som seksjon."""
    path = urlparse(entry.link).path  # f.eks. /samfunn/tittel/12345
    parts = [p for p in path.split("/") if p]
    return f"/{parts[0]}/" if parts else "/"


def fetch_feed(source: str) -> list[RSSArticle]:
    url = RSS_FEEDS.get(source)
    if not url:
        logger.error(f"Ukjent kilde: {source}")
        return []

    logger.info(f"Henter RSS fra {source}: {url}")
    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        summary = getattr(entry, "summary", "").strip()

        if not title or not link:
            continue

        if source == "vg":
            raw_cat = _extract_vg_category(entry)
        elif source == "aftenposten":
            raw_cat = _extract_aftenposten_category(entry)
        elif source == "e24":
            raw_cat = _extract_e24_category(entry)
        elif source == "morgenbladet":
            raw_cat = _extract_morgenbladet_category(entry)
        else:
            raw_cat = ""

        articles.append(RSSArticle(
            title=title,
            url=link,
            summary=summary,
            published=_parse_published(entry),
            source=source,
            raw_category=raw_cat,
        ))

    logger.info(f"  {len(articles)} artikler hentet fra {source}")
    return articles


def fetch_all_feeds() -> list[RSSArticle]:
    all_articles = []
    for source in ENABLED_SOURCES:
        if source not in RSS_FEEDS:
            logger.warning(f"Kilde '{source}' i ENABLED_SOURCES mangler RSS-URL i RSS_FEEDS, hopper over.")
            continue
        all_articles.extend(fetch_feed(source))
    return all_articles
