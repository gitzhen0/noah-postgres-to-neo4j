-- Docker init orchestrator. Runs the MVP schema + sample data + derived
-- tables in the correct order so a fresh `docker compose up` produces a
-- working PG that the rest of the pipeline can talk to.
--
-- Leaves the full NOAH ingest (Socrata housing_projects, ACS rent_burden,
-- zip_demographic) as explicit steps in the README — Docker init is only
-- responsible for the sample/minimum-viable path.
--
-- Files referenced here live one directory up in scripts/. They are sourced
-- via psql's \i meta-command so their canonical paths keep their original
-- names (no numeric prefixes polluting the real scripts directory).

\echo '[docker-init] 1/4 creating PostGIS-enabled schema...'
\i /srv/scripts/create_simple_schema.sql

\echo '[docker-init] 2/4 loading sample housing projects...'
\i /srv/scripts/load_sample_data.sql

\echo '[docker-init] 3/4 deriving zip_shapes from sample points...'
\i /srv/scripts/create_mock_zip_shapes.sql

\echo '[docker-init] 4/4 precomputing spatial relationships...'
\i /srv/scripts/precompute_spatial_relationships.sql

\echo '[docker-init] done — run scripts/load_demographics.py next to add ACS data.'
