# config.py - RSS-URLer og kategori-mappinger

CHROMIUM_EXECUTABLE = "/usr/bin/chromium-browser"
COOKIE_FILE = "/home/sconrads/.news-remarkable-cookies.json"
OUTPUT_DIR = "/home/sconrads/news-to-remarkable/output"
REMARKABLE_FOLDER = "/Nyheter"

# Navn som vises i tittelen på forsiden: "<OWNER_NAME>s nyhetsmorgen"
OWNER_NAME = "Stian"

# Antall dager før en PDF på reMarkable slettes automatisk
PDF_RETENTION_DAYS = 5

# Maks antall artikler per kategori (totalt, på tvers av kilder)
MAX_ARTICLES_PER_CATEGORY = 3

# Maks antall artikler per kategori per kilde (brukes ved RSS-henting, settes høyt for å gi rom til filtrering)
MAX_ARTICLES_PER_SOURCE = 8

# Minimum antall ord i artikkeltekst for å regnes som "god artikkel"
MIN_ARTICLE_WORDS = 300

# Maks alder på artikler (i dager). Artikler eldre enn dette filtreres bort fra RSS.
# Sett til None for å deaktivere aldersfiltrering.
MAX_ARTICLE_AGE_DAYS = 2

# Maks antall "siste nyheter"-overskrifter på forsiden
MAX_BREAKING_HEADLINES = 10

# Hvilke aviser som er aktive. Kommenter ut eller fjern for å deaktivere.
ENABLED_SOURCES = [
#    "vg",
    "aftenposten",
#    "e24",
    "morgenbladet",
]

RSS_FEEDS = {
    "vg": "https://www.vg.no/rss/feed/",
    "aftenposten": "https://www.aftenposten.no/rss/",
    "e24": "https://e24.no/rss/",
    "morgenbladet": "https://www.morgenbladet.no/rss",
}

# Mapping: din kategori -> hva vi leter etter i RSS fra hver avis
# VG og E24 bruker <category>-tag, Aftenposten bruker URL-sti
# Morgenbladet bruker URL-sti (f.eks. /samfunn/, /kultur/, /ideer/)
CATEGORY_MAP = {
    "Politikk": {
        "vg_categories": ["Nyheter"],
        "aftenposten_paths": ["/norge/", "/verden/", "/politikk/", "/meninger/"],
        "e24_categories": [],
        "morgenbladet_paths": ["/samfunn/", "/utenriks/", "/politikk/"],
    },
    "Økonomi": {
        "vg_categories": ["E24"],
        "aftenposten_paths": ["/e24/"],
        "e24_categories": [
            "Norsk økonomi", "Privatøkonomi", "Næringsliv",
            "Børs og finans", "Energi", "Eiendom",
        ],
        "morgenbladet_paths": ["/okonomi/"],
    },
    "Sport": {
        "vg_categories": ["Sport"],
        "aftenposten_paths": ["/sport/"],
        "e24_categories": [],
        "morgenbladet_paths": ["/sport/"],
    },
    "Teknologi": {
        "vg_categories": ["Teknologi"],
        "aftenposten_paths": ["/teknologi/", "/verden/"],
        "e24_categories": ["Teknologi"],
        "morgenbladet_paths": ["/teknologi/", "/vitenskap/"],
    },
    "Kultur": {
        "vg_categories": ["Rampelys", "Kultur"],
        "aftenposten_paths": ["/kultur/", "/underholdning/"],
        "e24_categories": [],
        "morgenbladet_paths": ["/kultur/", "/ideer/", "/boker/"],
    },
}

# Rekkefølge på kategorier i PDFen
CATEGORY_ORDER = ["Politikk", "Økonomi", "Sport", "Teknologi", "Kultur"]
