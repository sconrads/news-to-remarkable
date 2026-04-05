# news-to-remarkable

Henter artikler fra Aftenposten og Morgenbladet, genererer en PDF og sender den til et reMarkable-nettbrett. Kjøres automatisk kl. 06:00 hver morgen via GitHub Actions — ingen Raspberry Pi eller server nødvendig.

## Hva den gjør

1. Logger inn mot Schibsted SPID (Aftenposten) og Morgenbladet separat
2. Henter RSS-feeds fra aktiverte aviser
3. Kategoriserer artiklene (Politikk, Økonomi, Sport, Teknologi, Kultur)
4. Henter full artikkeltekst bak betalingsmur via autentiserte cookies
5. Genererer en stilren PDF tilpasset reMarkable (A4, ingen bilder, stor serif-font)
6. Laster opp PDFen til `/Nyheter`-mappen på reMarkable Cloud

## Kom i gang

Se [SETUP.md](SETUP.md) for fullstendig installasjonsveiledning.

**Kortversjon (GitHub Actions):**
1. Fork dette repoet (privat)
2. Hent rmapi device token: `python register.py`
3. Legg inn secrets i repoet ditt (Settings → Secrets → Actions)
4. Kjør workflowen manuelt fra Actions-fanen for å teste

## Forutsetninger

- GitHub-konto (for GitHub Actions-oppsett)
- Schibsted-konto med abonnement (Aftenposten, VG og/eller E24)
- Morgenbladet-konto med abonnement
- reMarkable-nettbrett koblet til reMarkable Cloud

## Secrets som må settes i GitHub

| Secret | Beskrivelse |
|---|---|
| `SCHIBSTED_EMAIL` | Din Schibsted-e-post (Aftenposten/VG) |
| `SCHIBSTED_PASSWORD` | Ditt Schibsted-passord |
| `RMAPI_DEVICE_TOKEN` | Device token fra `register.py` |
| `MORGENBLADET_EMAIL` | Din Morgenbladet-e-post (valgfritt) |
| `MORGENBLADET_PASSWORD` | Ditt Morgenbladet-passord (valgfritt) |
| `CALENDAR_ICS_URLS` | Kommaseparerte iCal-URLer (valgfritt) |
| `OWNER_NAME` | Ditt fornavn på forsiden (valgfritt) |

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
├── .github/
│   └── workflows/
│       └── daily-news.yml  # GitHub Actions workflow
├── templates/
│   └── newspaper.html   # HTML-mal for PDF-generering
└── fetcher/
    ├── auth.py          # Innlogging: Schibsted SPID + Morgenbladet
    ├── article.py       # Henter full artikkeltekst med cookies
    └── rss.py           # Henter og filtrerer RSS-feeds
```

## Kjøre lokalt / på Raspberry Pi

Se [SETUP.md](SETUP.md) for oppsett på lokal maskin eller Raspberry Pi.

```bash
cd ~/news-to-remarkable
PLAYWRIGHT_BROWSERS_PATH=~/news-to-remarkable/browsers venv/bin/python main.py
```

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

### GitHub Actions

Workflowen (`.github/workflows/daily-news.yml`) kjøres automatisk kl. 06:00 UTC daglig og kan også trigges manuelt. Den installerer alle avhengigheter, laster ned `rmapi`-binæren og skriver device token fra secrets til `~/.config/rmapi/rmapi.conf` ved hver kjøring. PDFen lastes også opp som artefakt i Actions og kan lastes ned direkte derfra.

### Schibsted SPID-innlogging

To-stegs flyt via `payment.schibsted.no`:

1. POST e-post + passord til `/authn/login`
2. `oauth/authorize` per avis (VG, Aftenposten, E24) for site-spesifikke sessions

### Morgenbladet-innlogging

Flyt via `auth.morgenbladet.no`:

1. Naviger til `morgenbladet.no`, lukk GDPR-popup
2. Klikk "Logg inn" → redirecter til `auth.morgenbladet.no`
3. Klikk "Logg inn uten Vipps" → velg "E-post"-tab
4. Fyll inn e-post → Neste → fyll inn passord → Enter

### reMarkable-opplasting

Bruker [`ddvk/rmapi`](https://github.com/ddvk/rmapi) v0.0.32. Enhet registreres mot reMarkable Cloud via [my.remarkable.com/device/remarkable](https://my.remarkable.com/device/remarkable) (klikk **Pair device**). Binæren er ikke inkludert i dette repoet — lastes ned automatisk av GitHub Actions.
