# categorizer.py - Mapper avisenes egne kategorier til brukerens kategorier

import logging
from collections import defaultdict

from config import CATEGORY_MAP, CATEGORY_ORDER, MAX_ARTICLES_PER_SOURCE
from fetcher.rss import RSSArticle

logger = logging.getLogger(__name__)


def _matches_category(article: RSSArticle, cat_name: str) -> bool:
    rules = CATEGORY_MAP.get(cat_name, {})
    src = article.source
    raw = article.raw_category

    if src == "vg":
        return raw in rules.get("vg_categories", [])
    elif src == "aftenposten":
        return any(raw == path for path in rules.get("aftenposten_paths", []))
    elif src == "e24":
        allowed = rules.get("e24_categories", [])
        if "*" in allowed:
            return True
        return raw in allowed
    elif src == "morgenbladet":
        return any(raw == path for path in rules.get("morgenbladet_paths", []))
    return False


def categorize(articles: list) -> dict:
    """
    Grupperer artikler etter brukerens kategorier.
    Returnerer dict: kategori -> liste med artikler (maks MAX_ARTICLES_PER_SOURCE per kilde,
    slik at vi har nok kandidater til kvalitetsfiltrering i main.py).
    """
    counts: dict = defaultdict(int)
    result: dict = {cat: [] for cat in CATEGORY_ORDER}

    for article in articles:
        for cat in CATEGORY_ORDER:
            if _matches_category(article, cat):
                key = (cat, article.source)
                if counts[key] < MAX_ARTICLES_PER_SOURCE:
                    result[cat].append(article)
                    counts[key] += 1
                break  # En artikkel tilhører kun én kategori

    for cat, arts in result.items():
        logger.info(f"  {cat}: {len(arts)} artikler")

    return result
