"""
Load ACS demographic seed (data/samples/acs_nyc_demographics.csv) into
PostgreSQL without requiring the psql client.

Creates zip_demographic table, stages the CSV, and inserts rows whose
zip_code matches a row in zip_shapes — producing exactly the 177 NYC zips
covered by the project's spatial data. Safe to rerun (ON CONFLICT UPDATE).

Usage:
    python scripts/load_demographics.py
    python scripts/load_demographics.py --csv path/to/other.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from noah_converter.utils.config import load_config  # noqa: E402

DDL = """
CREATE TABLE IF NOT EXISTS zip_demographic (
    zip_code               VARCHAR(10) PRIMARY KEY,
    total_population       INTEGER,
    median_age             NUMERIC(4, 1),
    total_housing_units    INTEGER,
    owner_occupied_units   INTEGER,
    renter_occupied_units  INTEGER,
    pct_renter_occupied    NUMERIC(5, 2),
    acs_vintage            VARCHAR(10) DEFAULT '2022',
    loaded_at              TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_zip_demographic_zip ON zip_demographic (zip_code);
"""

STAGE_DDL = """
-- Stage uses wide numeric types because the Census ACS API emits a
-- -666666666 sentinel for suppressed / zero-sample ZCTAs. We coerce
-- those to NULL in the MERGE step below.
CREATE TEMP TABLE _acs_stage (
    zip_code               VARCHAR(10),
    total_population       BIGINT,
    median_age             NUMERIC,
    total_housing_units    BIGINT,
    owner_occupied_units   BIGINT,
    renter_occupied_units  BIGINT,
    pct_renter_occupied    NUMERIC
) ON COMMIT DROP;
"""

# Census "null" sentinels
SENTINEL_NUM = -666666666

MERGE_SQL = """
INSERT INTO zip_demographic (
    zip_code, total_population, median_age, total_housing_units,
    owner_occupied_units, renter_occupied_units, pct_renter_occupied
)
SELECT
    s.zip_code,
    NULLIF(s.total_population,      -666666666)::integer       AS total_population,
    CASE WHEN s.median_age = -666666666 THEN NULL
         ELSE s.median_age::numeric(4,1) END                   AS median_age,
    NULLIF(s.total_housing_units,   -666666666)::integer       AS total_housing_units,
    NULLIF(s.owner_occupied_units,  -666666666)::integer       AS owner_occupied_units,
    NULLIF(s.renter_occupied_units, -666666666)::integer       AS renter_occupied_units,
    CASE WHEN s.pct_renter_occupied < 0 OR s.pct_renter_occupied > 100 THEN NULL
         ELSE s.pct_renter_occupied::numeric(5,2) END          AS pct_renter_occupied
FROM _acs_stage s
JOIN zip_shapes z ON s.zip_code = z.zip_code
ON CONFLICT (zip_code) DO UPDATE SET
    total_population      = EXCLUDED.total_population,
    median_age            = EXCLUDED.median_age,
    total_housing_units   = EXCLUDED.total_housing_units,
    owner_occupied_units  = EXCLUDED.owner_occupied_units,
    renter_occupied_units = EXCLUDED.renter_occupied_units,
    pct_renter_occupied   = EXCLUDED.pct_renter_occupied,
    loaded_at             = CURRENT_TIMESTAMP;
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).resolve().parent.parent
        / "data"
        / "samples"
        / "acs_nyc_demographics.csv",
    )
    args = ap.parse_args()

    if not args.csv.exists():
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        print(
            "Regenerate with: python scripts/fetch_acs_demographics.py",
            file=sys.stderr,
        )
        return 1

    cfg = load_config(None)
    dsn = {
        "host": cfg.source_db.host,
        "port": cfg.source_db.port,
        "dbname": cfg.source_db.database,
        "user": cfg.source_db.user,
        "password": cfg.source_db.password,
    }

    with psycopg2.connect(**dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.execute(STAGE_DDL)
            with args.csv.open("r") as f:
                cur.copy_expert(
                    "COPY _acs_stage FROM STDIN WITH (FORMAT csv, HEADER true)",
                    f,
                )
            cur.execute(MERGE_SQL)
            cur.execute("SELECT COUNT(*) FROM zip_demographic")
            count = cur.fetchone()[0]
            cur.execute(
                "SELECT AVG(total_population)::int, "
                "AVG(median_age)::numeric(4,1), "
                "AVG(pct_renter_occupied)::numeric(5,2) "
                "FROM zip_demographic"
            )
            avg_pop, avg_age, avg_pct = cur.fetchone()
        conn.commit()

    print(f"Loaded {count} rows into zip_demographic")
    print(f"  avg total_population:   {avg_pop:,}")
    print(f"  avg median_age:         {avg_age}")
    print(f"  avg pct_renter_occupied:{avg_pct}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
