# renderer.py - Bygger HTML fra mal og konverterer til PDF med WeasyPrint

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

from config import CATEGORY_ORDER, OUTPUT_DIR

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
SOURCE_LABELS = {
    "vg": "VG",
    "aftenposten": "Aftenposten",
    "e24": "E24",
    "morgenbladet": "Morgenbladet",
}


@dataclass
class ArticleView:
    title: str
    source_label: str
    published: Optional[str]
    summary: str
    full_text: str

    @property
    def paragraphs(self) -> list:
        return [p for p in self.full_text.split("\n\n") if p.strip()]


@dataclass
class CategoryView:
    name: str
    articles: list


@dataclass
class HeadlineView:
    title: str
    source_label: str
    published: Optional[str]


NORWEGIAN_MONTHS = [
    "", "januar", "februar", "mars", "april", "mai", "juni",
    "juli", "august", "september", "oktober", "november", "desember",
]


def _norwegian_date(dt: datetime, include_time: bool = False) -> str:
    month = NORWEGIAN_MONTHS[dt.month]
    if include_time:
        return f"{dt.day}. {month} {dt.year}, {dt.strftime('%H:%M')}"
    return f"{dt.day}. {month} {dt.year}"


def _format_date(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    return _norwegian_date(dt, include_time=True)


def build_html(categorized: dict, breaking_headlines: Optional[list] = None, calendar_events: Optional[list] = None) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("newspaper.html")

    categories = []
    for cat_name in CATEGORY_ORDER:
        articles_raw = categorized.get(cat_name, [])
        articles = [
            ArticleView(
                title=a.title,
                source_label=SOURCE_LABELS.get(a.source, a.source.upper()),
                published=_format_date(a.published),
                summary=a.summary,
                full_text=a.full_text,
            )
            for a in articles_raw
        ]
        categories.append(CategoryView(name=cat_name, articles=articles))

    headlines = []
    if breaking_headlines:
        for a in breaking_headlines:
            headlines.append(HeadlineView(
                title=a.title,
                source_label=SOURCE_LABELS.get(a.source, a.source.upper()),
                published=_format_date(a.published),
            ))

    from quotes import get_quote_of_the_day
    from config import OWNER_NAME
    quote_text, quote_author = get_quote_of_the_day()

    today = _norwegian_date(datetime.now())
    return template.render(
        categories=categories,
        date=today,
        owner_name=OWNER_NAME,
        breaking_headlines=headlines,
        quote_text=quote_text,
        quote_author=quote_author,
        calendar_events=calendar_events or [],
    )


def render_pdf(categorized: dict, breaking_headlines: Optional[list] = None, calendar_events: Optional[list] = None) -> str:
    """
    Bygger HTML fra Jinja2-mal og konverterer til PDF.
    Returnerer filsti til ferdig PDF.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    pdf_path = os.path.join(OUTPUT_DIR, f"Nyheter_{date_str}.pdf")

    logger.info("Bygger HTML ...")
    html_content = build_html(categorized, breaking_headlines=breaking_headlines, calendar_events=calendar_events)

    logger.info(f"Konverterer til PDF: {pdf_path}")
    HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(pdf_path)

    size_kb = os.path.getsize(pdf_path) // 1024
    logger.info(f"PDF ferdig: {pdf_path} ({size_kb} KB)")
    return pdf_path
