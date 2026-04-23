-- Load ACS 2022 5-year demographics for NYC ZCTAs into PostgreSQL.
--
-- Source: U.S. Census Bureau American Community Survey 5-year estimates,
-- 2022 vintage. Variables used:
--   B01003_001E  total population
--   B01002_001E  median age (years)
--   B25003_001E  total occupied housing units
--   B25003_002E  owner-occupied units
--   B25003_003E  renter-occupied units
--
-- The CSV under data/samples/acs_nyc_demographics.csv is a pre-fetched
-- snapshot that covers 186 ZCTAs across the NYC ranges. When joined
-- against zip_shapes (177 rows), produces 177 Demographic rows keyed by
-- zip_code. To refresh from the live Census API, run:
--   python scripts/fetch_acs_demographics.py

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

CREATE INDEX IF NOT EXISTS idx_zip_demographic_zip
    ON zip_demographic (zip_code);

-- Stage full ACS snapshot, then filter to zip_shapes to match project scope.
CREATE TEMP TABLE IF NOT EXISTS _acs_stage (
    zip_code               VARCHAR(10),
    total_population       INTEGER,
    median_age             NUMERIC(4, 1),
    total_housing_units    INTEGER,
    owner_occupied_units   INTEGER,
    renter_occupied_units  INTEGER,
    pct_renter_occupied    NUMERIC(5, 2)
);

-- \copy reads the CSV from the client (run this file via psql).
\copy _acs_stage FROM 'data/samples/acs_nyc_demographics.csv' WITH (FORMAT csv, HEADER true);

INSERT INTO zip_demographic (
    zip_code, total_population, median_age, total_housing_units,
    owner_occupied_units, renter_occupied_units, pct_renter_occupied
)
SELECT s.zip_code, s.total_population, s.median_age, s.total_housing_units,
       s.owner_occupied_units, s.renter_occupied_units, s.pct_renter_occupied
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

-- Sanity check
SELECT
    COUNT(*)                     AS demographic_rows,
    AVG(total_population)::int   AS avg_population,
    AVG(median_age)::numeric(4, 1) AS avg_median_age,
    AVG(pct_renter_occupied)::numeric(5, 2) AS avg_pct_renter
FROM zip_demographic;
