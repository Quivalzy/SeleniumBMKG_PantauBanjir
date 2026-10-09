"""Offline behavioral tests for the downloader; no requests reach BMKG."""

from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from io import BytesIO, StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import zipfile

import requests

import BMKG_API as bmkg


def workbook_bytes():
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as workbook:
        workbook.writestr("[Content_Types].xml", "<Types/>")
        workbook.writestr("xl/workbook.xml", "<workbook/>")
        workbook.writestr("xl/worksheets/sheet1.xml", "<worksheet/>")
    return buffer.getvalue()


def response(body=None, status=200, headers=None):
    result = MagicMock()
    result.__enter__.return_value = result
    result.status_code = status
    result.headers = headers or {"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    if status >= 400:
        result.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status}", response=result)
    payload = workbook_bytes() if body is None else body
    result.iter_content.return_value = [payload[:20], b"", payload[20:]]
    return result


class DateTests(unittest.TestCase):
    def test_clipped_leap_months(self):
        self.assertEqual(list(bmkg.iter_months(date(2016, 1, 15), date(2016, 3, 5))), [
            (date(2016, 1, 15), date(2016, 1, 31)),
            (date(2016, 2, 1), date(2016, 2, 29)),
            (date(2016, 3, 1), date(2016, 3, 5)),
        ])

    def test_months_cover_range_once(self):
        for start, end in [
            (date(2023, 2, 1), date(2023, 2, 28)),
            (date(2024, 2, 29), date(2024, 2, 29)),
            (date(2023, 12, 20), date(2024, 3, 3)),
            (date(2016, 1, 1), date(2026, 9, 30)),
        ]:
            with self.subTest(start=start, end=end):
                chunks = list(bmkg.iter_months(start, end))
                self.assertEqual(chunks[0][0], start)
                self.assertEqual(chunks[-1][1], end)
                for index, (first, last) in enumerate(chunks):
                    self.assertEqual((first.year, first.month), (last.year, last.month))
                    self.assertTrue(1 <= (last - first).days + 1 <= 31)
                    if index:
                        self.assertEqual(first, chunks[index - 1][1] + timedelta(days=1))
                self.assertEqual(sum((last - first).days + 1 for first, last in chunks), (end - start).days + 1)

    def test_invalid_configuration(self):
        for settings in [
            {"START_DATE": "2026-10-01", "END_DATE": "2026-09-30"},
            {"START_DATE": "2026-02-30"},
            {"START_DATE": "20260101"},
            {"END_DATE": "2027-01-01"},
            {"STATIONS": [{"type": "arg", "id": "../bad"}]},
            {"STATIONS": []},
        ]:
            with self.subTest(settings=settings), patch.multiple(bmkg, CURRENT_DATA_YEAR=2026, **settings):
                with self.assertRaises(ValueError):
                    bmkg.validate_config()

    def test_urls_and_paths(self):
        for instrument, station_id in [("arg", "150083"), ("aws", "STA2148"), ("aws", "STW1101")]:
            station = {"type": instrument, "id": station_id}
            for year, endpoint in [(2016, "downloadaccesdata_year/2016"), (2026, "downloadaccesdata_currentyear")]:
                first, last = date(year, 1, 1), date(year, 1, 31)
                self.assertEqual(bmkg.build_url(station, first, last, 2026),
                                 f"{bmkg.BASE_URL}/{endpoint}/{instrument}/{station_id}/{first}/{last}")
                self.assertEqual(bmkg.output_path("data", station, first, last),
                                 Path(f"data/{instrument}/{station_id}/{year}/{instrument}_{station_id}_{first}_{last}.xlsx"))
        with self.assertRaises(ValueError):
            bmkg.build_url(station, date(2025, 12, 1), date(2026, 1, 1), 2026)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.destination = Path(self.directory.name) / "station" / "sample.xlsx"
        self.session = MagicMock()
        self.url = "https://example.test/download"
        self.sleep = patch.object(bmkg.time, "sleep").start()
        self.addCleanup(patch.stopall)

    def download(self):
        with redirect_stdout(StringIO()):
            return bmkg.download_file(self.session, self.url, self.destination)

    def assert_no_temporary(self):
        self.assertFalse(self.destination.with_suffix(".xlsx.part").exists())

    def test_save_original_bytes_then_skip_without_request(self):
        self.session.get.return_value = response()
        self.assertEqual(self.download()[0], "saved")
        self.assertEqual(self.destination.read_bytes(), workbook_bytes())
        self.assert_no_temporary()
        self.session.get.assert_called_once_with(self.url, stream=True, timeout=bmkg.TIMEOUT)
        self.session.get.reset_mock()
        self.assertEqual(self.download()[0], "skipped")
        self.session.get.assert_not_called()

    def test_invalid_existing_file_is_replaced(self):
        self.destination.parent.mkdir()
        self.destination.write_bytes(b"truncated")
        self.session.get.return_value = response()
        self.assertEqual(self.download()[0], "saved")
        self.assertTrue(bmkg.valid_workbook(self.destination))

    def test_invalid_responses_do_not_leave_files(self):
        corrupt = workbook_bytes().replace(b"<worksheet/>", b"<worksheex/>")
        unrelated_zip = BytesIO()
        with zipfile.ZipFile(unrelated_zip, "w") as archive:
            archive.writestr("other.txt", "hello")
        for body, headers in [
            (b"", None), (b"<html>Error</html>", {"Content-Type": "text/html"}),
            (b'{"error":"no data"}', {"Content-Type": "application/json"}),
            (b"not excel", None), (corrupt, None), (unrelated_zip.getvalue(), None),
        ]:
            with self.subTest(body=body[:20]):
                self.session.get.return_value = response(body, headers=headers)
                self.assertEqual(self.download()[0], "failed")
                self.assertFalse(self.destination.exists())
                self.assert_no_temporary()

    def test_transient_http_and_network_errors_retry(self):
        for error in [response(status=500), response(status=429, headers={"Retry-After": "7"}),
                      requests.Timeout("timeout"), requests.ConnectionError("disconnected")]:
            with self.subTest(error=error):
                self.session.get.side_effect = [error, response()]
                self.assertEqual(self.download()[0], "saved")
                self.assert_no_temporary()
                self.destination.unlink()
        self.assertIn(unittest.mock.call(7), self.sleep.call_args_list)

    def test_permanent_http_failure_has_no_retry(self):
        self.session.get.return_value = response(status=403)
        self.assertEqual(self.download()[0], "failed")
        self.session.get.assert_called_once()
        self.sleep.assert_not_called()

    def test_missing_month_is_skipped_without_retry_or_file(self):
        for status in (204, 404):
            with self.subTest(status=status):
                self.session.get.reset_mock()
                missing = response(status=status)
                self.session.get.return_value = missing
                result, detail = self.download()
                self.assertEqual(result, "skipped")
                self.assertIn(f"HTTP {status}", detail)
                self.session.get.assert_called_once()
                missing.iter_content.assert_not_called()
                self.sleep.assert_not_called()
                self.assertFalse(self.destination.exists())
                self.assert_no_temporary()

    def test_main_skips_missing_month_and_downloads_next_month(self):
        self.session.get.side_effect = [response(status=404), response()]
        station = {"type": "arg", "id": "150083"}
        with patch.multiple(bmkg, START_DATE="2016-01-01", END_DATE="2016-02-29",
                            CURRENT_DATA_YEAR=2026, STATIONS=[station], OUTPUT_DIR=self.directory.name), \
                patch.object(bmkg.requests, "Session") as session_factory, redirect_stdout(StringIO()) as output:
            session_factory.return_value.__enter__.return_value = self.session
            self.assertEqual(bmkg.main(), 0)
            self.assertEqual(self.session.get.call_count, 2)
            self.assertIn("Saved: 1; skipped: 1; failed: 0", output.getvalue())
            january = bmkg.output_path(self.directory.name, station, date(2016, 1, 1), date(2016, 1, 31))
            february = bmkg.output_path(self.directory.name, station, date(2016, 2, 1), date(2016, 2, 29))
            self.assertFalse(january.exists())
            self.assertTrue(bmkg.valid_workbook(february))

    def test_exhausted_retries(self):
        self.session.get.side_effect = requests.Timeout("timeout")
        self.assertEqual(self.download()[0], "failed")
        self.assertEqual(self.session.get.call_count, bmkg.MAX_ATTEMPTS)
        self.assertEqual(self.sleep.call_args_list, [unittest.mock.call(1), unittest.mock.call(2)])
        self.assert_no_temporary()

    def test_interrupted_stream_retries_from_scratch(self):
        def broken_stream():
            yield b"partial data"
            raise requests.exceptions.ChunkedEncodingError("incomplete stream")
        broken = response()
        broken.iter_content.side_effect = lambda **kwargs: broken_stream()
        self.session.get.side_effect = [broken, response()]
        self.assertEqual(self.download()[0], "saved")
        self.assertEqual(self.destination.read_bytes(), workbook_bytes())
        self.assert_no_temporary()

    def test_keyboard_interrupt_cleans_partial_file(self):
        def interrupted_stream():
            yield b"partial data"
            raise KeyboardInterrupt()
        interrupted = response()
        interrupted.iter_content.side_effect = lambda **kwargs: interrupted_stream()
        self.session.get.return_value = interrupted
        with self.assertRaises(KeyboardInterrupt):
            self.download()
        self.assert_no_temporary()

    def test_retry_after_http_date(self):
        now = datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc)
        resp = response(status=429, headers={"Retry-After": format_datetime(now + timedelta(seconds=15))})
        with patch.object(bmkg, "datetime") as clock:
            clock.now.return_value = now
            self.assertEqual(bmkg.retry_delay(resp, 1), 15)
        self.assertEqual(bmkg.retry_delay(response(headers={"Retry-After": "invalid"}), 2), 2)

    def test_main_continues_after_failure_and_reports_nonzero(self):
        stations = [{"type": "arg", "id": "150083"}, {"type": "aws", "id": "STA2148"}]
        with patch.multiple(bmkg, START_DATE="2026-09-01", END_DATE="2026-09-30",
                            CURRENT_DATA_YEAR=2026, STATIONS=stations), \
                patch.object(bmkg, "download_file", side_effect=[("failed", "HTTP 403"), ("saved", "file.xlsx")]) as download, \
                patch.object(bmkg.requests, "Session"), redirect_stdout(StringIO()) as output:
            self.assertEqual(bmkg.main(), 1)
            self.assertEqual(download.call_count, 2)
            self.assertIn("Saved: 1; skipped: 0; failed: 1", output.getvalue())


if __name__ == "__main__":
    unittest.main()
