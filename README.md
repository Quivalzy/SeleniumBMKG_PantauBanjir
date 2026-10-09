# SeleniumBMKG_PantauBanjir
A repository containing script to automate data scraping from BMKG and Pantau Banjir Jakarta

## BMKG API downloads

`BMKG_API.py` downloads the original BMKG Excel workbooks directly, without a
browser, login, or authentication token.

Install the only external dependency in your Python environment:

```bash
python3 -m pip install requests
```

Edit the configuration at the top of `BMKG_API.py`:

- `START_DATE` and `END_DATE`: inclusive dates in `YYYY-MM-DD` format. The default
  range is `2016-01-01` through `2026-09-30`.
- `STATIONS`: defaults to ARG Karangsembung (`150083`), ARG Malahayu (`150302`),
  and AWS Bantarkawung (`STA2148`). Each entry has a lowercase `type`, string
  `id`, and optional display `name`.
- `OUTPUT_DIR`: defaults to `bmkg_data` alongside the script.
- `CURRENT_DATA_YEAR`: defaults to the execution year. That year uses
  `downloadaccesdata_currentyear`; older years use `downloadaccesdata_year/{year}`. Change
  this setting if BMKG changes its archive cutoff. Dates beyond this year are
  rejected. Routing follows this rule without automatically switching endpoints.
- `DELAY`, `TIMEOUT`, and `MAX_ATTEMPTS`: default to a 0.5-second pause between
  downloads, 10/120-second connection/read timeouts, and three total attempts.

Run:

```bash
python3 BMKG_API.py
```

The script splits the range into calendar months, clipping the first and last
months to your dates. Every request covers at most 31 inclusive days; leap years
and year boundaries are handled automatically. For example, `2016-01-15` through
`2016-03-05` produces January 15–31, February 1–29, and March 1–5 for each station.

Files are saved as:

```text
bmkg_data/arg/150083/2016/arg_150083_2016-01-15_2016-01-31.xlsx
```

Filenames use the requested dates rather than BMKG's download-date filename.
Downloads stream to temporary `.xlsx.part` files and are renamed after Excel
ZIP structure and CRC validation. Valid existing files are skipped on reruns;
invalid files are downloaded again. Returned workbooks are preserved without
merging, filtering, or removing workbooks that contain no observations.

Network interruptions, HTTP 429, and HTTP 5xx responses are retried with backoff
and `Retry-After` support. HTTP 404 (Not Found) and 204 (No Content) are counted
as skipped months without retries or empty files; the script moves to the next
month. Missing months are checked again on later runs. Other errors, including
unexpected HTML/JSON or corrupt downloads, are reported and the remaining downloads
continue. The final summary lists saved, skipped, and failed files. Exit codes:
`0` for completion without failures, `1` for configuration/download failures,
and `130` for interruption. A later rerun retries failures and skips valid files.
Use a completed end date, or remove the relevant file before rerunning if you
want to refresh a month that was still receiving observations.

Run the offline tests (no BMKG requests):

```bash
python3 -m unittest discover -s tests -v
```
