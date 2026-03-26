# fetcher/calendar.py - Henter hendelser fra ICS/iCal-URLer for dagens dato
#
# Støtter flere kalendere via kommaseparert liste i CALENDAR_ICS_URLS (.env).
# Håndterer:
#   - Heldagshendelser (DATE-verdier uten tidspunkt)
#   - Tidsbegrensede hendelser (DATETIME-verdier, med tidssone)
#   - Recurring events støttes ikke (kun DTSTART-dato sjekkes)

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional

import requests
from icalendar import Calendar

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    title: str
    start_time: Optional[str]   # "HH:MM" eller None for heldagshendelser
    end_time: Optional[str]     # "HH:MM" eller None for heldagshendelser
    location: Optional[str]
    all_day: bool

    def time_label(self) -> str:
        """Returnerer lesbar tidsetikett: 'Hele dagen', '14:00' eller '14:00–15:30'."""
        if self.all_day:
            return "Hele dagen"
        if self.start_time and self.end_time:
            return f"{self.start_time}–{self.end_time}"
        if self.start_time:
            return self.start_time
        return ""


def _to_date(dt_value) -> Optional[date]:
    """Konverterer icalendar-verdi til date, uavhengig av om det er date eller datetime."""
    if dt_value is None:
        return None
    if isinstance(dt_value, datetime):
        # Konverter til lokal tid hvis tidssone-bevisst
        if dt_value.tzinfo is not None:
            dt_value = dt_value.astimezone().replace(tzinfo=None)
        return dt_value.date()
    if isinstance(dt_value, date):
        return dt_value
    return None


def _to_time_str(dt_value) -> Optional[str]:
    """Returnerer 'HH:MM'-streng fra datetime, eller None for date-verdier."""
    if dt_value is None:
        return None
    if isinstance(dt_value, datetime):
        if dt_value.tzinfo is not None:
            dt_value = dt_value.astimezone().replace(tzinfo=None)
        return dt_value.strftime("%H:%M")
    return None  # rein date — heldagshendelse


def _fetch_events_from_url(url: str, today: date) -> list:
    """Henter og parser én ICS-URL. Returnerer liste med CalendarEvent for i dag."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Kunne ikke hente kalender fra {url[:60]}...: {e}")
        return []

    try:
        cal = Calendar.from_ical(resp.content)
    except Exception as e:
        logger.warning(f"Kunne ikke parse ICS fra {url[:60]}...: {e}")
        return []

    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        dtstart = component.get("DTSTART")
        if dtstart is None:
            continue
        dtstart_val = dtstart.dt

        event_date = _to_date(dtstart_val)
        if event_date != today:
            continue

        summary = str(component.get("SUMMARY", "Uten tittel")).strip()
        location_raw = component.get("LOCATION")
        location = str(location_raw).strip() if location_raw else None

        start_time = _to_time_str(dtstart_val)

        dtend_raw = component.get("DTEND")
        end_time = _to_time_str(dtend_raw.dt) if dtend_raw else None

        all_day = not isinstance(dtstart_val, datetime)

        events.append(CalendarEvent(
            title=summary,
            start_time=start_time,
            end_time=end_time,
            location=location,
            all_day=all_day,
        ))

    logger.info(f"  {len(events)} hendelser i dag fra {url[:60]}...")
    return events


def fetch_todays_events() -> list:
    """
    Henter alle hendelser for dagens dato fra CALENDAR_ICS_URLS (env).
    CALENDAR_ICS_URLS er en kommaseparert liste med ICS-URLer.
    Returnerer en sortert liste med CalendarEvent (heldagshendelser sist).
    """
    raw = os.getenv("CALENDAR_ICS_URLS", "").strip()
    if not raw:
        logger.info("CALENDAR_ICS_URLS ikke satt — hopper over kalender.")
        return []

    urls = [u.strip() for u in raw.split(",") if u.strip()]
    today = date.today()
    logger.info(f"Henter kalender for {today} fra {len(urls)} kilde(r) ...")

    all_events = []
    for url in urls:
        all_events.extend(_fetch_events_from_url(url, today))

    # Sorter: tidsbegrensede hendelser (med klokkeslett) først, sortert på tid
    # Heldagshendelser samles til slutt
    timed = sorted(
        [e for e in all_events if not e.all_day],
        key=lambda e: e.start_time or "",
    )
    all_day = [e for e in all_events if e.all_day]

    return timed + all_day
