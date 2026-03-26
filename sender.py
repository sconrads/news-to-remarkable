#!/usr/bin/env python3
# sender.py - Laster opp PDF til reMarkable Cloud via rmapi (ddvk/rmapi v0.0.32+)

import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

logger = logging.getLogger(__name__)

RMAPI = str(Path(__file__).parent / "rmapi")


def _rmapi(*args, input_text=None) -> tuple:
    """Kjør rmapi med gitte argumenter. Returnerer (returncode, stdout, stderr)."""
    cmd = [RMAPI, "-ni"] + list(args)
    logger.debug(f"rmapi: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=input_text,
        timeout=120,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _ensure_folder(folder_name: str) -> str:
    """
    Sjekker om mappen finnes; oppretter den hvis ikke.
    Returnerer mappestien (f.eks. '/Nyheter').
    folder_name er f.eks. '/Nyheter' eller 'Nyheter'.
    """
    name = folder_name.strip("/")
    remote_path = f"/{name}"

    rc, out, err = _rmapi("ls", remote_path)
    if rc == 0:
        logger.info(f"Mappe '{remote_path}' finnes allerede.")
        return remote_path

    logger.info(f"Oppretter mappe '{remote_path}' på reMarkable ...")
    rc, out, err = _rmapi("mkdir", remote_path)
    if rc != 0:
        raise RuntimeError(f"Kunne ikke opprette mappe '{remote_path}': {err or out}")

    logger.info(f"Mappe '{remote_path}' opprettet.")
    return remote_path


def cleanup_old_pdfs() -> None:
    """
    Sletter PDF-filer i REMARKABLE_FOLDER som er eldre enn PDF_RETENTION_DAYS dager.
    Forventer filnavn på formatet 'Nyheter_YYYY-MM-DD'.
    """
    from config import REMARKABLE_FOLDER, PDF_RETENTION_DAYS
    days = PDF_RETENTION_DAYS

    if not Path(RMAPI).exists():
        logger.warning("rmapi-binær ikke funnet — hopper over opprydding.")
        return

    cutoff = datetime.now() - timedelta(days=days)

    rc, out, err = _rmapi("ls", REMARKABLE_FOLDER)
    if rc != 0:
        logger.warning(f"Kunne ikke liste filer i '{REMARKABLE_FOLDER}': {err or out}")
        return

    for line in out.splitlines():
        # rmapi ls returnerer linjer som f.eks. "[d] Nyheter_2026-03-20"
        # eller bare "Nyheter_2026-03-20" avhengig av versjon
        name = line.strip().lstrip("[df] ").strip()
        # Hent siste del etter mellomrom (håndterer "[d] navn" og "navn")
        parts = line.strip().split()
        if not parts:
            continue
        name = parts[-1]

        if not name.startswith("Nyheter_"):
            continue

        date_part = name.replace("Nyheter_", "")
        try:
            file_date = datetime.strptime(date_part, "%Y-%m-%d")
        except ValueError:
            continue

        if file_date < cutoff:
            remote_path = f"{REMARKABLE_FOLDER}/{name}"
            logger.info(f"Sletter gammel PDF: {remote_path} ({date_part})")
            rc2, out2, err2 = _rmapi("rm", remote_path)
            if rc2 == 0:
                logger.info(f"  Slettet: {remote_path}")
            else:
                logger.warning(f"  Kunne ikke slette '{remote_path}': {err2 or out2}")


def upload_to_remarkable(pdf_path: str) -> bool:
    """
    Laster opp PDFen til reMarkable Cloud via rmapi.
    Returnerer True ved suksess, False ved feil.

    Bruker REMARKABLE_FOLDER fra config (standard: /Nyheter).
    rmapi må være plassert i samme mappe som sender.py.
    """
    from config import REMARKABLE_FOLDER

    if not Path(RMAPI).exists():
        logger.error(f"rmapi-binær ikke funnet: {RMAPI}")
        return False

    if not Path(pdf_path).exists():
        logger.error(f"PDF-fil ikke funnet: {pdf_path}")
        return False

    try:
        remote_folder = _ensure_folder(REMARKABLE_FOLDER)

        logger.info(f"Laster opp '{pdf_path}' til '{remote_folder}' ...")
        rc, out, err = _rmapi("put", "--force", pdf_path, remote_folder)

        if rc != 0:
            raise RuntimeError(f"rmapi put feilet (rc={rc}): {err or out}")

        logger.info(f"Opplasting vellykket! {out}")
        return True

    except subprocess.TimeoutExpired:
        logger.error("rmapi tidsavbrudd etter 120 sekunder.")
        return False
    except Exception as e:
        logger.error(f"Feil ved opplasting til reMarkable: {e}")
        return False
