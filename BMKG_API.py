"""Download BMKG raw-data Excel workbooks in calendar-month chunks."""

from calendar import monthrange
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import re
import time
import zipfile
import zlib

import requests


# --- Configuration: edit these settings before running ---
START_DATE = "2026-09-01"
END_DATE = "2026-09-30"
OUTPUT_DIR = Path(__file__).resolve().parent / "bmkg_data"
CURRENT_DATA_YEAR = date.today().year
STATIONS = [
    {"type": "aws", "id": "STW1101", "name": "MAWS Panciran"},
]
DELAY = 0.5  # Seconds between station/month downloads.
TIMEOUT = (10, 120)  # Connection timeout, read timeout (seconds).
MAX_ATTEMPTS = 3  # Includes the first attempt.
BASE_URL = "https://apiaws.bmkg.go.id/rawdata"


def parse_date(value):
    """Require an ISO calendar date rather than silently accepting other formats."""
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Dates must use YYYY-MM-DD format")
    return date.fromisoformat(value)


def validate_config():
    start, end = parse_date(START_DATE), parse_date(END_DATE)
    if start > end:
        raise ValueError("START_DATE must be on or before END_DATE")
    if not isinstance(CURRENT_DATA_YEAR, int) or not 1 <= CURRENT_DATA_YEAR <= 9999:
        raise ValueError("CURRENT_DATA_YEAR must be a valid calendar year")
    if end.year > CURRENT_DATA_YEAR:
        raise ValueError("END_DATE cannot be beyond CURRENT_DATA_YEAR")
    if not STATIONS:
        raise ValueError("STATIONS must contain at least one station")
    seen = set()
    for station in STATIONS:
        instrument, station_id = station.get("type", ""), station.get("id", "")
        if not isinstance(instrument, str) or not re.fullmatch(r"[a-z]+", instrument):
            raise ValueError("Station type must contain lowercase letters (e.g. arg or aws)")
        if not isinstance(station_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", station_id):
            raise ValueError("Station ID must be a nonempty string of letters, digits, _ or -")
        if (instrument, station_id) in seen:
            raise ValueError(f"Duplicate station: {instrument}/{station_id}")
        seen.add((instrument, station_id))
    if not isinstance(MAX_ATTEMPTS, int) or MAX_ATTEMPTS < 1:
        raise ValueError("MAX_ATTEMPTS must be a positive integer")
    if DELAY < 0 or len(TIMEOUT) != 2 or any(value <= 0 for value in TIMEOUT):
        raise ValueError("DELAY must be nonnegative and both TIMEOUT values must be positive")
    return start, end


def iter_months(start, end):
    """Yield inclusive monthly ranges clipped to the requested dates."""
    if start > end:
        raise ValueError("Start date must be on or before end date")
    current = start
    while current <= end:
        month_end = date(current.year, current.month, monthrange(current.year, current.month)[1])
        chunk_end = min(month_end, end)
        yield current, chunk_end
        if chunk_end == end:
            break
        current = (date(current.year + 1, 1, 1) if current.month == 12
                   else date(current.year, current.month + 1, 1))


def build_url(station, start, end, current_data_year):
    """Select the current-data or year-specific archive endpoint."""
    if start > end or (start.year, start.month) != (end.year, end.month):
        raise ValueError("Each download must stay within one calendar month")
    if end.year > current_data_year:
        raise ValueError("Requested dates cannot be beyond the current-data year")
    endpoint = ("downloadaccesdata_currentyear" if start.year == current_data_year
                else f"downloadaccesdata_year/{start.year}")
    return f"{BASE_URL}/{endpoint}/{station['type']}/{station['id']}/{start}/{end}"


def output_path(output_dir, station, start, end):
    filename = f"{station['type']}_{station['id']}_{start}_{end}.xlsx"
    return Path(output_dir) / station["type"] / station["id"] / str(start.year) / filename


def valid_workbook(path):
    """Check the Excel ZIP structure and CRCs without transforming the data."""
    try:
        with zipfile.ZipFile(path) as workbook:
            names = set(workbook.namelist())
            return (
                {"[Content_Types].xml", "xl/workbook.xml"}.issubset(names)
                and any(name.startswith("xl/worksheets/") and name.endswith(".xml") for name in names)
                and workbook.testzip() is None
            )
    except (OSError, zipfile.BadZipFile, RuntimeError, EOFError, zlib.error, NotImplementedError):
        return False


def retry_delay(response, attempt):
    """Use Retry-After seconds or an HTTP date; otherwise back off 1, 2, ... seconds."""
    if response is not None:
        value = response.headers.get("Retry-After", "")
        try:
            return max(0, int(value))
        except (ValueError, TypeError):
            try:
                when = parsedate_to_datetime(value)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                return max(0, (when - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return 2 ** (attempt - 1)


def download_file(session, url, destination):
    """Return (saved/skipped/failed, detail), leaving only validated final files."""
    destination = Path(destination)
    if valid_workbook(destination):
        return "skipped", str(destination)
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            response = None
            wait = None
            try:
                with session.get(url, stream=True, timeout=TIMEOUT) as response:
                    if response.status_code in (204, 404):
                        return "skipped", f"No file available for this station/range (HTTP {response.status_code})"
                    response.raise_for_status()
                    if response.status_code != 200:
                        raise ValueError(f"Unexpected HTTP status {response.status_code}")
                    content_type = response.headers.get("Content-Type", "").lower()
                    if any(kind in content_type for kind in ("text/html", "json")):
                        raise ValueError(f"Expected an Excel file, received {content_type}")
                    with temporary.open("wb") as target:
                        for chunk in response.iter_content(chunk_size=64 * 1024):
                            if chunk:
                                target.write(chunk)
                    if not valid_workbook(temporary):
                        raise ValueError("Response is empty, corrupt, or not an Excel workbook")
                    temporary.replace(destination)
                    return "saved", str(destination)
            except requests.RequestException as error:
                retryable = (
                    isinstance(error, (requests.ConnectionError, requests.Timeout,
                                       requests.exceptions.ChunkedEncodingError,
                                       requests.exceptions.ContentDecodingError))
                    or (isinstance(error, requests.HTTPError) and response is not None
                        and (response.status_code == 429 or 500 <= response.status_code <= 599))
                )
                if not retryable or attempt == MAX_ATTEMPTS:
                    return "failed", str(error)
                wait = retry_delay(response, attempt)
                print(f"    [RETRY] Attempt {attempt}/{MAX_ATTEMPTS}: {error}; waiting {wait:.1f}s")
            except (OSError, ValueError) as error:
                return "failed", str(error)
            finally:
                temporary.unlink(missing_ok=True)
            if wait is not None:
                time.sleep(wait)
    except OSError as error:
        return "failed", str(error)


def main():
    try:
        start, end = validate_config()
    except (ValueError, TypeError, AttributeError) as error:
        print(f"[CONFIG ERROR] {error}")
        return 1

    months = list(iter_months(start, end))
    total = len(months) * len(STATIONS)
    totals = {"saved": 0, "skipped": 0, "failed": 0}
    print(f"BMKG: {start} through {end}; {len(STATIONS)} stations; {total} files")
    print(f"Output: {Path(OUTPUT_DIR).resolve()}")
    try:
        with requests.Session() as session:
            session.headers.update({"User-Agent": "BMKG-API-Downloader/1.0"})
            index = 0
            for station in STATIONS:
                for chunk_start, chunk_end in months:
                    index += 1
                    label = station.get("name") or f"{station['type']}/{station['id']}"
                    print(f"[{index}/{total}] {label}: {chunk_start} through {chunk_end}")
                    url = build_url(station, chunk_start, chunk_end, CURRENT_DATA_YEAR)
                    destination = output_path(OUTPUT_DIR, station, chunk_start, chunk_end)
                    status, detail = download_file(session, url, destination)
                    totals[status] += 1
                    print(f"    [{status.upper()}] {detail}")
                    if index < total:
                        time.sleep(DELAY)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Run again to resume; valid files will be skipped.")
        print(f"Saved: {totals['saved']}; skipped: {totals['skipped']}; failed: {totals['failed']}")
        return 130

    print(f"Finished. Saved: {totals['saved']}; skipped: {totals['skipped']}; failed: {totals['failed']}")
    return 1 if totals["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
