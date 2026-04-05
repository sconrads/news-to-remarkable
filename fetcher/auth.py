# fetcher/auth.py - Schibsted SPID og Morgenbladet Piano-autentisering via Playwright
#
# Schibsted innloggingsflyt (oppdaget 2026-03):
#   1. POST e-post + passord til payment.schibsted.no/authn/login (SPID SDK v4)
#   2. oauth/authorize for VG, Aftenposten og E24 — etablerer site-spesifikke sessions
#   3. Alle cookies lagres til COOKIE_FILE og gjenbrukes til neste dag
#
# Morgenbladet innloggingsflyt:
#   1. Navigerer til morgenbladet.no og klikker "Logg inn"
#   2. Piano-popup: fyller inn e-post og passord
#   3. Cookies lagres til MORGENBLADET_COOKIE_FILE
#
# Kjente Schibsted klient-ID-er og redirect-URIer:
#   VG:           4ef1cfb0e962dd2e0d8d0000  ->  https://www.vg.no/auth/callback
#   Aftenposten:  520204a6411c7a8838000000  ->  https://www.aftenposten.no/seksjon/paywall-redirect
#   E24:          4d46b0cd74dea2fd799a0000  ->  https://e24.no/auth/callback

import json
import logging
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

COOKIE_FILE = os.getenv("COOKIE_FILE", str(Path.home() / ".news-remarkable-cookies.json"))
MORGENBLADET_COOKIE_FILE = os.getenv(
    "MORGENBLADET_COOKIE_FILE", str(Path.home() / ".news-remarkable-cookies-morgenbladet.json")
)
BROWSERS_PATH = os.getenv("PLAYWRIGHT_BROWSERS_PATH", str(Path(__file__).parent.parent / "browsers"))

# Initiell innlogging: bruker VGs klient for å starte SPID-flyten
_LOGIN_URL = (
    "https://payment.schibsted.no/authn/login"
    "?client_id=4ef1cfb0e962dd2e0d8d0000"
    "&redirect_uri=https%3A%2F%2Fwww.vg.no%2Fauth%2Fcallback"
    "&response_type=code"
    "&scope=openid+email+profile"
    "&acr_values=password"
    "&prompt=login"
)

# OAuth authorize-URLer for å etablere site-spesifikke sessions
_OAUTH_URLS = [
    # VG
    (
        "https://payment.schibsted.no/oauth/authorize"
        "?client_id=4ef1cfb0e962dd2e0d8d0000"
        "&redirect_uri=https%3A%2F%2Fwww.vg.no%2Fauth%2Fcallback"
        "&response_type=code"
        "&scope=openid+email+profile"
    ),
    # Aftenposten
    (
        "https://payment.schibsted.no/oauth/authorize"
        "?client_id=520204a6411c7a8838000000"
        "&redirect_uri=https%3A%2F%2Fwww.aftenposten.no%2Fseksjon%2Fpaywall-redirect"
        "&response_type=code"
        "&scope=openid"
    ),
    # E24
    (
        "https://payment.schibsted.no/oauth/authorize"
        "?client_id=4d46b0cd74dea2fd799a0000"
        "&redirect_uri=https%3A%2F%2Fe24.no%2Fauth%2Fcallback"
        "&response_type=code"
        "&scope=openid+email+profile"
    ),
]


def _save_cookies(cookies: list, path: str) -> None:
    Path(path).write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
    logger.info(f"Cookies lagret til {path}")


def _load_cookies(path: str) -> list:
    p = Path(path)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except Exception:
        return []


def login(email: str, password: str) -> list:
    """
    Logger inn via Schibsted SPID og returnerer alle session-cookies
    for VG, Aftenposten og E24.
    """
    logger.info("Logger inn mot Schibsted SPID ...")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = BROWSERS_PATH

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        try:
            # --- Steg 1: Logg inn med e-post + passord ---
            logger.info("Navigerer til Schibsted-innlogging ...")
            page.goto(_LOGIN_URL, wait_until="networkidle", timeout=30000)

            page.wait_for_selector("input#email-input", timeout=15000)
            page.fill("input#email-input", email)
            page.keyboard.press("Enter")

            page.wait_for_selector("input[type='password']", timeout=15000)
            page.fill("input[type='password']", password)
            page.keyboard.press("Enter")

            # Vent til SPID-flyten er ferdig (lander på profile-pages eller redirecter)
            time.sleep(6)
            logger.info(f"Etter innlogging: {page.url[:80]}")

            # --- Steg 2: Etabler site-spesifikke sessions via oauth/authorize ---
            for oauth_url in _OAUTH_URLS:
                site = "vg" if "vg.no" in oauth_url else ("aftenposten" if "aftenposten" in oauth_url else "e24")
                logger.info(f"Etablerer {site}-session ...")
                try:
                    page.goto(oauth_url, wait_until="networkidle", timeout=20000)
                    time.sleep(2)
                    logger.info(f"  {site} landet på: {page.url[:80]}")
                except PlaywrightTimeoutError:
                    logger.warning(f"  Timeout for {site} OAuth, fortsetter ...")

            cookies = context.cookies()
            _save_cookies(cookies, COOKIE_FILE)
            logger.info(f"Innlogging vellykket — {len(cookies)} cookies lagret.")
            return cookies

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout under innlogging: {e}")
            raise
        finally:
            browser.close()


def get_authenticated_cookies(email: str, password: str) -> list:
    """
    Returnerer gyldige cookies — fra cache hvis mulig, ellers logger inn på nytt.
    """
    cookies = _load_cookies(COOKIE_FILE)
    if cookies:
        logger.info(f"Gjenbruker {len(cookies)} lagrede cookies.")
        return cookies
    return login(email, password)


def invalidate_cookies() -> None:
    """Slett lagrede cookies slik at neste kall logger inn på nytt."""
    path = Path(COOKIE_FILE)
    if path.exists():
        path.unlink()
        logger.info("Cookies slettet.")


def login_morgenbladet(email: str, password: str) -> list:
    """
    Logger inn mot Morgenbladet via auth.morgenbladet.no og returnerer session-cookies.

    Innloggingsflyt (oppdaget 2026-03):
      1. Naviger til morgenbladet.no
      2. Lukk GDPR-popup (Sourcepoint CMP iframe på cmp.morgenbladet.no)
      3. Klikk p.text.login-avatar — redirecter til auth.morgenbladet.no
      4. Klikk "Logg inn uten Vipps" — viser fane-form (Mobilnummer / E-post)
      5. Klikk "E-post"-tab (button[data-testid='email'])
      6. Fyll inn e-post, klikk "Neste"
      7. Fyll inn passord, trykk Enter — redirecter tilbake til morgenbladet.no
    """
    logger.info("Logger inn mot Morgenbladet ...")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = BROWSERS_PATH

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        try:
            # --- Steg 1: Naviger til morgenbladet.no ---
            logger.info("Navigerer til Morgenbladet ...")
            page.goto("https://www.morgenbladet.no", wait_until="domcontentloaded", timeout=60000)

            # --- Steg 2: Lukk GDPR-popup (Sourcepoint CMP i iframe) ---
            try:
                cmp_iframe = None
                for f in page.frames:
                    if "cmp.morgenbladet.no" in f.url or "sourcepoint" in f.url:
                        cmp_iframe = f
                        break
                if cmp_iframe:
                    logger.info("GDPR-popup funnet, lukker ...")
                    cmp_iframe.click(
                        "button:has-text('Godta alle'), button:has-text('Accept all')",
                        timeout=5000,
                    )
                    time.sleep(1)
                else:
                    page.click(
                        "button:has-text('Godta alle'), button:has-text('Accept all'), "
                        "button:has-text('Godta'), button[title*='Godta']",
                        timeout=3000,
                    )
                    time.sleep(1)
            except PlaywrightTimeoutError:
                logger.info("Ingen GDPR-popup funnet eller allerede lukket.")

            # --- Steg 3: Klikk "Logg inn" → redirecter til auth.morgenbladet.no ---
            logger.info("Klikker 'Logg inn' ...")
            page.locator("p.text.login-avatar").click(timeout=10000)
            time.sleep(3)
            logger.info(f"Landet på: {page.url[:80]}")

            # --- Steg 4: Klikk "Logg inn uten Vipps" ---
            logger.info("Klikker 'Logg inn uten Vipps' ...")
            page.click("button:has-text('Logg inn uten Vipps')", timeout=10000)
            time.sleep(1)

            # --- Steg 5: Klikk "E-post"-tab ---
            logger.info("Klikker E-post-tab ...")
            page.click("button[data-testid='email']", timeout=10000)
            time.sleep(1)

            # --- Steg 6: Fyll inn e-post og klikk "Neste" ---
            logger.info("Fyller inn e-post ...")
            page.wait_for_selector("input[type='email']", timeout=10000)
            page.fill("input[type='email']", email)
            page.click("button:has-text('Neste')", timeout=10000)
            time.sleep(3)
            logger.info(f"Etter e-post: {page.url[:80]}")

            # --- Steg 7: Fyll inn passord og trykk Enter ---
            logger.info("Fyller inn passord ...")
            page.wait_for_selector("input[type='password']", timeout=10000)
            page.fill("input[type='password']", password)
            with page.expect_navigation(timeout=15000):
                page.keyboard.press("Enter")

            time.sleep(3)
            logger.info(f"Etter innlogging: {page.url[:80]}")

            cookies = context.cookies()
            _save_cookies(cookies, MORGENBLADET_COOKIE_FILE)
            logger.info(f"Morgenbladet-innlogging vellykket — {len(cookies)} cookies lagret.")
            return cookies

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout under Morgenbladet-innlogging: {e}")
            raise
        finally:
            browser.close()


def get_morgenbladet_cookies(email: str, password: str) -> list:
    """
    Returnerer gyldige Morgenbladet-cookies — fra cache hvis mulig, ellers logger inn på nytt.
    """
    cookies = _load_cookies(MORGENBLADET_COOKIE_FILE)
    if cookies:
        logger.info(f"Gjenbruker {len(cookies)} lagrede Morgenbladet-cookies.")
        return cookies
    return login_morgenbladet(email, password)


def invalidate_morgenbladet_cookies() -> None:
    """Slett lagrede Morgenbladet-cookies."""
    path = Path(MORGENBLADET_COOKIE_FILE)
    if path.exists():
        path.unlink()
        logger.info("Morgenbladet-cookies slettet.")
