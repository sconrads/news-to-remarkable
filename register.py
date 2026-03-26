#!/usr/bin/env python3
# register.py - Engangsskript: registrerer denne maskinen mot reMarkable Cloud API v2
#
# Kjør én gang:
#   python register.py
#
# Krever at du har hentet en engangskoble fra:
#   https://my.remarkable.com/connect/desktop

import os
import sys
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

ENV_FILE = Path(__file__).parent / ".env"
DEVICE_TOKEN_KEY = "REMARKABLE_DEVICE_TOKEN"

AUTH_HOST = "https://webapp-prod.cloud.remarkable.engineering"
DEVICE_REGISTER_URL = f"{AUTH_HOST}/token/json/2/device/new"


def register_device(otp: str) -> str:
    """
    Registrerer enheten med en engangskoble og returnerer device token (JWT).
    """
    device_id = str(uuid.uuid4())
    payload = {
        "code": otp.strip(),
        "deviceDesc": "desktop-windows",
        "deviceID": device_id,
    }

    print(f"  Sender registreringsforespørsel (deviceID={device_id}) ...")
    resp = requests.post(
        DEVICE_REGISTER_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if resp.status_code == 200:
        token = resp.text.strip()
        if not token:
            print("FEIL: Serveren returnerte tom token.")
            sys.exit(1)
        return token
    elif resp.status_code == 400:
        print("FEIL: Ugyldig eller utløpt engangskoble (HTTP 400).")
        print(f"  Svar: {resp.text[:200]}")
        sys.exit(1)
    else:
        print(f"FEIL: Uventet HTTP-status {resp.status_code}.")
        print(f"  Svar: {resp.text[:200]}")
        sys.exit(1)


def save_token(token: str) -> None:
    """Lagrer device token i .env-filen."""
    if not ENV_FILE.exists():
        ENV_FILE.touch()
    set_key(str(ENV_FILE), DEVICE_TOKEN_KEY, token)
    print(f"  Device token lagret til {ENV_FILE}")


def main():
    load_dotenv(ENV_FILE)

    existing = os.getenv(DEVICE_TOKEN_KEY, "")
    if existing:
        print(f"Det finnes allerede en {DEVICE_TOKEN_KEY} i {ENV_FILE}.")
        answer = input("Vil du registrere på nytt? [j/N] ").strip().lower()
        if answer not in ("j", "ja", "y", "yes"):
            print("Avbryter.")
            sys.exit(0)

    print()
    print("=" * 60)
    print("reMarkable Cloud - Enhetsregistrering")
    print("=" * 60)
    print()
    print("1. Gå til: https://my.remarkable.com/connect/desktop")
    print("2. Du vil se en engangskoble (8 tegn, f.eks. 'abcd1234').")
    print("3. Skriv inn koden nedenfor.")
    print()

    otp = input("Engangskoble: ").strip()
    if not otp:
        print("FEIL: Ingen kode oppgitt.")
        sys.exit(1)

    print()
    token = register_device(otp)
    save_token(token)

    print()
    print("Registrering vellykket!")
    print()
    print("Neste steg:")
    print("  - Kjør 'python list_folders.py' for å se mappene dine på reMarkable.")
    print("  - Finn ID-en til 'Nyheter'-mappen (eller opprett den på nettbrettet først).")
    print(f"  - Legg til 'REMARKABLE_FOLDER_ID=<id>' i {ENV_FILE}")
    print("  - La feltet stå tomt for å laste opp til rotnivå.")
    print()


if __name__ == "__main__":
    main()
