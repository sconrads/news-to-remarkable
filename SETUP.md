# Installasjonsveiledning

Steg-for-steg for å sette opp news-to-remarkable på en Raspberry Pi (ARM64, Debian 11 Bullseye).

## 1. Forberedelser

### På reMarkable-nettbrettet

Opprett en mappe kalt `Nyheter` direkte på nettbrettet. PDFene vil bli lastet opp hit.

### På Raspberry Pi

Logg inn via SSH og opprett prosjektmappen:

```bash
mkdir -p ~/news-to-remarkable
```

## 2. Hent koden

Koden synkroniseres fra utviklingsmaskinen med rsync (Pi har ikke git). Se [Oppdatere Pi](#oppdatere-pi) nedenfor for rsync-kommandoen.

## 3. Opprett virtuelt miljø og installer avhengigheter

```bash
cd ~/news-to-remarkable
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

## 4. Installer Playwright-nettleser

Playwright krever en headless Chromium-nettleser. Installer den i prosjektmappen slik at den ikke kolliderer med systemets Chromium:

```bash
PLAYWRIGHT_BROWSERS_PATH=~/news-to-remarkable/browsers \
  venv/bin/playwright install chromium
```

Verifiser at binæren ble installert:

```bash
ls ~/news-to-remarkable/browsers/
```

Du skal se en mappe som `chromium-XXXX/`.

## 5. Konfigurer miljøvariabler

```bash
cp .env.example .env
nano .env
```

Fyll inn:

```
SCHIBSTED_EMAIL=din@email.no
SCHIBSTED_PASSWORD=dittpassord
MORGENBLADET_EMAIL=din@email.no
MORGENBLADET_PASSWORD=dittpassord
```

Lagre og lukk (`Ctrl+O`, `Enter`, `Ctrl+X`).

## 6. Last ned rmapi

Last ned `rmapi` ARM64-binæren fra [github.com/ddvk/rmapi/releases](https://github.com/ddvk/rmapi/releases):

```bash
cd ~/news-to-remarkable
wget https://github.com/ddvk/rmapi/releases/download/v0.0.32/rmapi-arm64.tar.gz
tar -xzf rmapi-arm64.tar.gz
chmod +x rmapi
rm rmapi-arm64.tar.gz
```

Verifiser:

```bash
./rmapi version
```

## 7. Registrer mot reMarkable Cloud

Dette steget gjøres kun én gang. Du trenger en engangskode fra reMarkable:

1. Gå til [my.remarkable.com/connect/desktop](https://my.remarkable.com/connect/desktop)
2. Du vil se en 8-tegns kode (f.eks. `abcd1234`)
3. Kjør registreringsskriptet og skriv inn koden:

```bash
venv/bin/python register.py
```

Tokenet lagres automatisk i `~/.config/rmapi/rmapi.conf`.

Verifiser at tilkoblingen fungerer:

```bash
./rmapi ls /
```

Du skal se mappene på reMarkable-nettbrettet ditt.

## 8. Test kjøring

Kjør appen manuelt for å verifisere at alt fungerer:

```bash
cd ~/news-to-remarkable
PLAYWRIGHT_BROWSERS_PATH=~/news-to-remarkable/browsers venv/bin/python main.py
```

Forventet output (forkortet):

```
2026-03-25 06:00:01 [INFO] main: === Starter nyhetsinnhenting ===
2026-03-25 06:00:01 [INFO] main: Henter Schibsted-cookies ...
2026-03-25 06:00:03 [INFO] main: Henter Morgenbladet-cookies ...
2026-03-25 06:00:05 [INFO] main: Henter RSS-feeds ...
2026-03-25 06:00:06 [INFO] main: Totalt 36 artikler etter kategorisering
2026-03-25 06:00:06 [INFO] main: Henter full artikkeltekst ...
2026-03-25 06:02:30 [INFO] main: Genererer PDF ...
2026-03-25 06:02:40 [INFO] main: Sender til reMarkable ...
2026-03-25 06:02:42 [INFO] main: === Ferdig! PDF sendt til reMarkable. ===
```

## 9. Sett opp cron-jobb

Åpne crontab-editoren:

```bash
crontab -e
```

Legg til denne linjen for å kjøre appen kl. 06:00 hver morgen:

```
0 6 * * * cd ~/news-to-remarkable && PLAYWRIGHT_BROWSERS_PATH=~/news-to-remarkable/browsers ~/news-to-remarkable/venv/bin/python main.py >> ~/news-to-remarkable/cron.log 2>&1
```

Verifiser at cron-jobben er registrert:

```bash
crontab -l
```

Loggfilen skrives til `~/news-to-remarkable/cron.log`. Sjekk den etter første automatiske kjøring.

---

## Oppdatere Pi

Koden vedlikeholdes med git på utviklingsmaskinen og synkroniseres til Pi med rsync. Pi har ikke git installert.

**Arbeidsflyt:**

1. Gjør endringer og commit på utviklingsmaskinen
2. Push til GitHub: `git push`
3. Rsync til Pi:

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

4. Verifiser med en manuell kjøring på Pi:

```bash
ssh pi@<pi-ip> \
  "cd ~/news-to-remarkable && PLAYWRIGHT_BROWSERS_PATH=~/news-to-remarkable/browsers venv/bin/python main.py 2>&1"
```

**Merk:** `.env`, `venv/`, `browsers/`, `rmapi` og `output/` synkroniseres aldri — disse finnes kun på Pi.

**Hvis du legger til nye Python-pakker** (`requirements.txt` er endret), må du installere på Pi også:

```bash
ssh pi@<pi-ip> \
  "cd ~/news-to-remarkable && venv/bin/pip install -r requirements.txt"
```

---

## Feilsøking

### Innlogging feiler mot Schibsted

- Sjekk at e-post og passord i `.env` er korrekte
- Slett cookie-cachen og prøv igjen: `rm ~/.news-remarkable-cookies.json`
- Playwright-nettleseren må være installert i `~/news-to-remarkable/browsers/`

### Innlogging feiler mot Morgenbladet

- Sjekk at `MORGENBLADET_EMAIL` og `MORGENBLADET_PASSWORD` i `.env` er korrekte
- Slett cookie-cachen: `rm ~/.news-remarkable-cookies-morgenbladet.json`
- Morgenbladet-innloggingsflyten: `morgenbladet.no` → `auth.morgenbladet.no` → "Logg inn uten Vipps" → "E-post"-tab

### rmapi feiler

- Verifiser at `rmapi`-binæren er kjørbar: `ls -la ~/news-to-remarkable/rmapi`
- Sjekk at device-token finnes: `cat ~/.config/rmapi/rmapi.conf`
- Prøv manuell listing: `~/news-to-remarkable/rmapi ls /`
- Token kan utløpe — kjør `register.py` på nytt for å re-registrere

### PDF genereres ikke

- Sjekk at `output/`-mappen finnes: `mkdir -p ~/news-to-remarkable/output`
- WeasyPrint krever noen systembiblioteker: `sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0`

### Playwright finner ikke Chromium

Sett miljøvariabelen eksplisitt:

```bash
PLAYWRIGHT_BROWSERS_PATH=~/news-to-remarkable/browsers venv/bin/python main.py
```

Eller reinstaller nettleseren:

```bash
PLAYWRIGHT_BROWSERS_PATH=~/news-to-remarkable/browsers venv/bin/playwright install chromium
```
