"""
Refresh the ACS demographic snapshot used to seed zip_demographic.

Fetches ACS 5-year estimates from the U.S. Census Bureau for NYC ZCTAs and
writes data/samples/acs_nyc_demographics.csv. The CSV is a superset of the
177 zips in zip_shapes; the SQL loader (load_demographics.sql) filters it
on join.

Usage:
    python scripts/fetch_acs_demographics.py [--vintage 2022] [--out PATH]

No API key is required for un-rate-limited use below ~500 requests/day.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.request
from pathlib import Path

# NYC ZCTA ranges (superset — non-NYC zips won't return data).
NYC_ZIP_RANGES = [
    range(10001, 10045),  # Manhattan
    range(10065, 10076),
    range(10103, 10104),
    range(10119, 10120),
    range(10128, 10132),
    range(10280, 10283),
    range(10301, 10315),  # Staten Island
    range(10451, 10476),  # Bronx
    range(11004, 11010),  # Queens
    range(11101, 11110),
    range(11351, 11436),
    range(11691, 11698),
    range(11201, 11257),  # Brooklyn
]

# ACS variables
VARS = [
    ("B01003_001E", "total_population"),
    ("B01002_001E", "median_age"),
    ("B25003_001E", "total_housing_units"),
    ("B25003_002E", "owner_occupied_units"),
    ("B25003_003E", "renter_occupied_units"),
]


def _build_zip_list() -> list[str]:
    return sorted({f"{z:05d}" for r in NYC_ZIP_RANGES for z in r})


def _fetch_chunk(vintage: int, zips: list[str]) -> list[list[str]]:
    get = ",".join(v for v, _ in VARS)
    url = (
        f"https://api.census.gov/data/{vintage}/acs/acs5"
        f"?get=NAME,{get}"
        f"&for=zip%20code%20tabulation%20area:{','.join(zips)}"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        payload = json.loads(resp.read())
    return payload[1:]  # drop header row


def _pct_renter(renter: str, total: str) -> str:
    try:
        total_i = int(total) if total not in (None, "", "null") else 0
        renter_i = int(renter) if renter not in (None, "", "null") else 0
        if total_i <= 0:
            return "0.00"
        return f"{renter_i / total_i * 100:.2f}"
    except (ValueError, TypeError):
        return "0.00"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vintage", type=int, default=2022)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("data/samples/acs_nyc_demographics.csv"),
    )
    ap.add_argument("--chunk", type=int, default=50)
    args = ap.parse_args()

    zips = _build_zip_list()
    print(f"Querying ACS {args.vintage} 5-year for {len(zips)} candidate ZCTAs...")

    rows: list[list[str]] = []
    for i in range(0, len(zips), args.chunk):
        chunk = zips[i : i + args.chunk]
        got = _fetch_chunk(args.vintage, chunk)
        print(f"  chunk {i // args.chunk + 1}: {len(got)} ZCTAs returned")
        rows.extend(got)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "zip_code",
                "total_population",
                "median_age",
                "total_housing_units",
                "owner_occupied_units",
                "renter_occupied_units",
                "pct_renter_occupied",
            ]
        )
        for _name, pop, age, total, owner, renter, zcta in rows:
            w.writerow(
                [
                    zcta,
                    pop or "",
                    age or "",
                    total or "",
                    owner or "",
                    renter or "",
                    _pct_renter(renter, total),
                ]
            )

    print(f"Wrote {len(rows)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
