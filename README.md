# news-to-remarkable

Automatisk nyhetsapp som henter artikler fra Aftenposten og Morgenbladet, genererer en PDF og sender den til et reMarkable-nettbrett. Kjøres som en nattlig cron-jobb (kl. 06:00) på en Raspberry Pi.

## Hva den gjør

1. Logger inn mot Schibsted SPID (Aftenposten) og Morgenbladet separat
2. Henter RSS-feeds fra aktiverte aviser
3. Kategoriserer artiklene (Politikk, Økonomi, Sport, Teknologi, Kultur)
4. Henter full artikkeltekst bak betalingsmur via autentiserte cookies
5. Genererer en stilren PDF tilpasset reMarkable (A4, ingen bilder, stor serif-font)
6. Laster opp PDFen til `/Nyheter`-mappen på reMarkable Cloud

## Forutsetninger

- Raspberry Pi (ARM64, Debian 11 Bullseye) — eller annen Linux-maskin
- Python 3.9+
- Schibsted-konto med abonnement (Aftenposten, VG og/eller E24)
- Morgenbladet-konto med abonnement
- reMarkable-nettbrett koblet til reMarkable Cloud

## Kom i gang

Se [SETUP.md](SETUP.md) for fullstendig installasjonsveiledning.

## Kjøre manuelt

```bash
cd ~/news-to-remarkable
PLAYWRIGHT_BROWSERS_PATH=~/news-to-remarkable/browsers venv/bin/python main.py
```

## Oppdatere Pi med ny kode

Koden lever i git på utviklingsmaskinen og synkroniseres til Pi med rsync (Pi har ikke git installert).

**Fra utviklingsmaskinen:**

```bash
rsync -av \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='browsers' \
  --exclude='rmapi' \
  --exclude='output' \
  --exclude='__pycache__' \
  --exclude='.env' \
  --exclude='*.pyc' \
  /path/to/news-to-remarkable/ \
  pi@<pi-ip>:~/news-to-remarkable/
```

Etter rsync kan du kjøre appen manuelt på Pi for å verifisere:

```bash
ssh pi@<pi-ip> \
  "cd ~/news-to-remarkable && PLAYWRIGHT_BROWSERS_PATH=~/news-to-remarkable/browsers venv/bin/python main.py 2>&1"
```

## Velge aviser

Rediger `ENABLED_SOURCES` i `config.py` for å slå aviser av og på:

```python
ENABLED_SOURCES = [
#   "vg",
    "aftenposten",
#   "e24",
    "morgenbladet",
]
```

## Prosjektstruktur

```
news-to-remarkable/
├── main.py              # Koordinerer hele flyten
├── config.py            # RSS-URLer, kategori-mappinger, innstillinger
├── categorizer.py       # Sorterer artikler i kategorier
├── renderer.py          # Genererer PDF via WeasyPrint
├── sender.py            # Laster opp til reMarkable via rmapi
├── register.py          # Engangsskript: registrerer mot reMarkable Cloud
├── requirements.txt     # Python-avhengigheter
├── .env.example         # Mal for miljøvariabler
├── templates/
│   └── newspaper.html   # HTML-mal for PDF-generering
└── fetcher/
    ├── auth.py          # Innlogging: Schibsted SPID + Morgenbladet
    ├── article.py       # Henter full artikkeltekst med cookies
    └── rss.py           # Henter og filtrerer RSS-feeds
```

## Konfigurasjon

Kopier `.env.example` til `.env` og fyll inn:

```
SCHIBSTED_EMAIL=din@email.no
SCHIBSTED_PASSWORD=dittpassord
MORGENBLADET_EMAIL=din@email.no
MORGENBLADET_PASSWORD=dittpassord
```

Innstillinger som aktiverte aviser, kategorier og antall artikler justeres i `config.py`.

## Avhengigheter

| Pakke | Bruk |
|-------|------|
| `playwright` | Innlogging (headless Chromium) |
| `feedparser` | Parsing av RSS-feeds |
| `beautifulsoup4` | Parsing av artikkeltekst fra HTML |
| `weasyprint` | PDF-generering fra HTML |
| `jinja2` | HTML-maling |
| `requests` | HTTP-kall |
| `python-dotenv` | Lese `.env`-filer |

## Tekniske detaljer

### Schibsted SPID-innlogging

To-stegs flyt via `payment.schibsted.no`:

1. POST e-post + passord til `/authn/login`
2. `oauth/authorize` per avis (VG, Aftenposten, E24) for site-spesifikke sessions

Cookies caches i `~/.news-remarkable-cookies.json` og gjenbrukes til neste dag.

### Morgenbladet-innlogging

Flyt via `auth.morgenbladet.no`:

1. Naviger til `morgenbladet.no`, lukk GDPR-popup
2. Klikk "Logg inn" → redirecter til `auth.morgenbladet.no`
3. Klikk "Logg inn uten Vipps" → velg "E-post"-tab
4. Fyll inn e-post → Neste → fyll inn passord → Enter

Cookies caches i `~/.news-remarkable-cookies-morgenbladet.json`.

### reMarkable-opplasting

Bruker [`ddvk/rmapi`](https://github.com/ddvk/rmapi) v0.0.32 ARM64-binær. Binæren plasseres i prosjektmappen og er ikke inkludert i dette repoet.
