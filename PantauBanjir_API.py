import requests
import pandas as pd
from datetime import datetime, timedelta
from calendar import monthrange
import os
import time

# --- Configuration ---
START_DATE = datetime(2026, 1, 1)
END_DATE   = datetime(2026, 5, 31)
OUTPUT_DIR = "water_level_data"
DELAY      = 0.3  # seconds between requests

HEADERS = {
    "accept":             "application/json, text/plain, */*",
    "accept-language":    "en-US,en;q=0.9",
    "connection":         "keep-alive",
    "dnt":                "1",
    "origin":             "https://pantaubanjir.jakarta.go.id",
    "referer":            "https://pantaubanjir.jakarta.go.id/",
    "sec-ch-ua":          '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile":   "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest":     "empty",
    "sec-fetch-mode":     "cors",
    "sec-fetch-site":     "same-site",
    "token":              "T4EgIr1xIwsy7vr9UiAY64L61HWlDVN4V6qE3cc7OCvGzEg4hqhiagqatihAFgGB",
    "user-agent":         "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
}

BASE_URL = "https://sisteminformasibanjir.jakarta.go.id/api/report"

ENDPOINTS = {
    "pintu_air":      "pintuAirReports",
    "pos_pengamatan": "posPengamatanReports",
    "rumah_pompa":    "rumahPompaReports",
}

# Maps json_normalize dot-notation keys → clean column names
COLUMN_MAPS = {
    "pintu_air": {
        "id":               "id",
        "tanggal":          "tanggal",
        "jam":              "jam",
        "pintu_air.id":     "pintu_air_id",
        "pintu_air.name":   "pintu_air_nama",
        "pintu_air.aliran": "aliran",
        "pintu_air.cctv":   "cctv_url",
        "ketinggian":       "ketinggian_cm",
        "bukaan":           "bukaan",
        "status_siaga":     "status_siaga",
        "cuaca.inisial":    "cuaca_inisial",
        "cuaca.nama":       "cuaca_nama",
    },
    "pos_pengamatan": {
        "id":                    "id",
        "tanggal":               "tanggal",
        "jam":                   "jam",
        "pos_pengamatan.id":     "pos_id",
        "pos_pengamatan.name":   "pos_nama",
        "pos_pengamatan.aliran": "aliran",
        "ketinggian":            "ketinggian_cm",
        "status_siaga":          "status_siaga",
        "cuaca.inisial":         "cuaca_inisial",
        "cuaca.nama":            "cuaca_nama",
    },
    "rumah_pompa": {
        "id":                         "id",
        "tanggal":                    "tanggal",
        "jam":                        "jam",
        "pompa_air.id":               "pompa_air_id",
        "pompa_air.name":             "pompa_air_nama",
        "pompa_air.kewenangan":       "kewenangan",
        "pompa_air.kapasitas":        "kapasitas_m3s",
        "pompa_air.jumlah_operator":  "jumlah_operator",
        "pompa_air.jumlah_pintu_air": "jumlah_pintu_air",
        "pompa_air.jumlah_genset":    "jumlah_genset",
        "tma":                        "tma_cm",
        "total_pompa":                "total_pompa",
        "pompa_operasi":              "pompa_operasi",
        "pompa_siaga":                "pompa_siaga",
        "cuaca.inisial":              "cuaca_inisial",
        "cuaca.nama":                 "cuaca_nama",
    },
}

# Preferred column order per type (station → time → measurement → status → weather)
COLUMN_ORDER = {
    "pintu_air": [
        "pintu_air_id", "pintu_air_nama", "aliran",
        "tanggal", "jam",
        "ketinggian_cm", "bukaan", "status_siaga",
        "cuaca_inisial", "cuaca_nama", "cctv_url", "id",
    ],
    "pos_pengamatan": [
        "pos_id", "pos_nama", "aliran",
        "tanggal", "jam",
        "ketinggian_cm", "status_siaga",
        "cuaca_inisial", "cuaca_nama", "id",
    ],
    "rumah_pompa": [
        "pompa_air_id", "pompa_air_nama", "kewenangan",
        "tanggal", "jam",
        "tma_cm", "total_pompa", "pompa_operasi", "pompa_siaga",
        "kapasitas_m3s", "jumlah_operator", "jumlah_pintu_air", "jumlah_genset",
        "cuaca_inisial", "cuaca_nama", "id",
    ],
}


def fetch_daily(endpoint_key: str, date: datetime) -> pd.DataFrame:
    date_str = date.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/{ENDPOINTS[endpoint_key]}/{date_str}?format=json"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", [])

        if not data:
            return pd.DataFrame()

        df = pd.json_normalize(data)
        df = df.rename(columns=COLUMN_MAPS[endpoint_key])
        ordered = [c for c in COLUMN_ORDER[endpoint_key] if c in df.columns]
        return df[ordered]

    except requests.exceptions.RequestException as e:
        print(f"    [WARN] {endpoint_key} {date_str}: {e}")
        return pd.DataFrame()


def iter_days(start: datetime, end: datetime):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def iter_months(start: datetime, end: datetime):
    cur = datetime(start.year, start.month, 1)
    while cur <= end:
        last_day = monthrange(cur.year, cur.month)[1]
        yield max(cur, start), min(datetime(cur.year, cur.month, last_day), end)
        cur = datetime(cur.year + 1, 1, 1) if cur.month == 12 else datetime(cur.year, cur.month + 1, 1)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for month_start, month_end in iter_months(START_DATE, END_DATE):
        month_label = month_start.strftime("%Y_%m")
        print(f"\n{'='*52}")
        print(f"  {month_start.strftime('%B %Y')}")
        print(f"{'='*52}")

        month_data = {key: [] for key in ENDPOINTS}

        for day in iter_days(month_start, month_end):
            day_str = day.strftime("%Y-%m-%d")
            print(f"  {day_str}", end="", flush=True)

            for key in ENDPOINTS:
                df = fetch_daily(key, day)
                if not df.empty:
                    month_data[key].append(df)
                time.sleep(DELAY)

            print(" ✓")

        for key, frames in month_data.items():
            if not frames:
                print(f"  [SKIP] {key}: no data for {month_label}")
                continue

            combined = pd.concat(frames, ignore_index=True)
            out_path = os.path.join(OUTPUT_DIR, f"{key}_{month_label}.xlsx")
            combined.to_excel(out_path, index=False)
            print(f"  [OK]   {key}_{month_label}.xlsx  ({len(combined):,} rows)")


if __name__ == "__main__":
    main()
