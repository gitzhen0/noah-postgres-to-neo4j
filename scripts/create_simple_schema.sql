-- Simplified NOAH Schema for MVP Testing
-- Only core tables with essential fields

-- Enable PostGIS (should already be enabled)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Table 1: Housing Projects (Main entity table)
-- Simplified version with only essential fields
CREATE TABLE IF NOT EXISTS housing_projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) UNIQUE NOT NULL,
    project_name TEXT,
    borough VARCHAR(50),
    zipcode VARCHAR(10),

    -- Address
    street_address TEXT,

    -- Geographic coordinates
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    geom GEOMETRY(POINT, 4326),

    -- Project details
    completion_date DATE,

    -- Unit counts (simplified)
    total_units INTEGER DEFAULT 0,
    affordable_units INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index
CREATE INDEX IF NOT EXISTS idx_housing_projects_geom ON housing_projects USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_housing_projects_zipcode ON housing_projects (zipcode);
CREATE INDEX IF NOT EXISTS idx_housing_projects_borough ON housing_projects (borough);

-- Function to update geometry from lat/lon
CREATE OR REPLACE FUNCTION update_housing_geometry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update geometry
DROP TRIGGER IF EXISTS trigger_update_housing_geometry ON housing_projects;
CREATE TRIGGER trigger_update_housing_geometry
    BEFORE INSERT OR UPDATE ON housing_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_housing_geometry();

-- Table 2: ZIP Code Summary (Aggregated data by ZIP)
-- This will be our second main entity
CREATE TABLE IF NOT EXISTS zip_summary (
    zipcode VARCHAR(10) PRIMARY KEY,
    borough VARCHAR(50),

    -- Counts
    total_projects INTEGER DEFAULT 0,
    total_units INTEGER DEFAULT 0,
    total_affordable_units INTEGER DEFAULT 0,

    -- Averages
    avg_units_per_project DECIMAL(10, 2),

    -- Geographic center (centroid)
    center_lat DECIMAL(10, 8),
    center_lon DECIMAL(11, 8),

    -- Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_zip_summary_borough ON zip_summary (borough);

-- Table 3: Borough Summary (Even higher level aggregation)
CREATE TABLE IF NOT EXISTS borough_summary (
    borough VARCHAR(50) PRIMARY KEY,

    -- Counts
    total_zipcodes INTEGER DEFAULT 0,
    total_projects INTEGER DEFAULT 0,
    total_units INTEGER DEFAULT 0,
    total_affordable_units INTEGER DEFAULT 0,

    -- Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- View: Quick stats
CREATE OR REPLACE VIEW project_stats AS
SELECT
    COUNT(*) as total_projects,
    COUNT(DISTINCT zipcode) as total_zipcodes,
    COUNT(DISTINCT borough) as total_boroughs,
    SUM(total_units) as total_units,
    SUM(affordable_units) as total_affordable_units,
    AVG(total_units) as avg_units_per_project
FROM housing_projects;

COMMENT ON TABLE housing_projects IS 'Affordable housing projects in NYC';
COMMENT ON TABLE zip_summary IS 'Aggregated statistics by ZIP code';
COMMENT ON TABLE borough_summary IS 'Aggregated statistics by borough';
