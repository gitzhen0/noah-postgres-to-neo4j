-- ============================================================
-- PostGIS Spatial Relationships Precomputation
-- ============================================================
-- 目的：在 PostgreSQL 中预计算所有空间关系，
--       因为 Neo4j 不支持 POLYGON 和复杂几何计算
-- ============================================================

\echo '🗺️  Starting spatial relationships precomputation...'
\echo ''

-- ============================================================
-- Step 1: ZIP Code Centroids (中心点)
-- ============================================================
\echo '📍 Step 1: Computing ZIP code centroids...'

DROP TABLE IF EXISTS zip_centroids CASCADE;

CREATE TABLE zip_centroids AS
SELECT
    zip_code,
    ST_Y(ST_Centroid(geom)) AS center_lat,
    ST_X(ST_Centroid(geom)) AS center_lon,
    ST_AsText(geom) AS geometry_wkt,           -- 保存 WKT 格式供外部 GIS 工具
    ST_Area(geom::geography) / 1000000.0 AS area_km2,  -- 面积（平方公里）
    ST_Perimeter(geom::geography) / 1000.0 AS perimeter_km  -- 周长（公里）
FROM zip_shapes
WHERE geom IS NOT NULL;

-- 添加索引
CREATE INDEX idx_zip_centroids_code ON zip_centroids(zip_code);

-- 验证
DO $$
DECLARE
    centroid_count INTEGER;
    zip_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO centroid_count FROM zip_centroids;
    SELECT COUNT(*) INTO zip_count FROM zip_shapes WHERE geom IS NOT NULL;

    RAISE NOTICE '   ✓ Created % centroids from % ZIP shapes', centroid_count, zip_count;

    IF centroid_count != zip_count THEN
        RAISE WARNING '   ⚠️  Mismatch: % centroids vs % ZIP shapes', centroid_count, zip_count;
    END IF;
END $$;

\echo ''

-- ============================================================
-- Step 2: ZIP Neighbors (邻接关系) - 核心！
-- ============================================================
\echo '🔗 Step 2: Computing ZIP neighbor relationships...'
\echo '   (This may take a few minutes for 177 ZIPs...)'

DROP TABLE IF EXISTS zip_neighbors CASCADE;

CREATE TABLE zip_neighbors AS
SELECT
    a.zip_code AS from_zip,
    b.zip_code AS to_zip,

    -- 距离计算（使用 centroids，单位：公里）
    ST_Distance(
        ST_Centroid(a.geom)::geography,
        ST_Centroid(b.geom)::geography
    ) / 1000.0 AS distance_km,

    -- 是否物理接壤
    ST_Touches(a.geom, b.geom) AS is_adjacent,

    -- 是否有重叠（数据质量检查）
    ST_Overlaps(a.geom, b.geom) AS has_overlap,

    -- 共享边界长度（如果接壤）
    CASE
        WHEN ST_Touches(a.geom, b.geom) THEN
            ST_Length(ST_Intersection(ST_Boundary(a.geom), ST_Boundary(b.geom))::geography) / 1000.0
        ELSE 0
    END AS shared_boundary_km

FROM zip_shapes a
CROSS JOIN zip_shapes b
WHERE
    a.zip_code < b.zip_code  -- 避免重复和自连接
    AND a.geom IS NOT NULL
    AND b.geom IS NOT NULL
    AND (
        -- 只保留以下情况之一：
        ST_Touches(a.geom, b.geom)  -- 1. 物理接壤
        OR ST_DWithin(a.geom::geography, b.geom::geography, 10000)  -- 2. 10km 内
    );

-- 添加索引
CREATE INDEX idx_zip_neighbors_from ON zip_neighbors(from_zip);
CREATE INDEX idx_zip_neighbors_to ON zip_neighbors(to_zip);
CREATE INDEX idx_zip_neighbors_adjacent ON zip_neighbors(is_adjacent);
CREATE INDEX idx_zip_neighbors_distance ON zip_neighbors(distance_km);

-- 验证和统计
DO $$
DECLARE
    total_neighbors INTEGER;
    adjacent_count INTEGER;
    nearby_count INTEGER;
    avg_distance NUMERIC;
    max_distance NUMERIC;
BEGIN
    SELECT COUNT(*) INTO total_neighbors FROM zip_neighbors;
    SELECT COUNT(*) INTO adjacent_count FROM zip_neighbors WHERE is_adjacent = true;
    SELECT COUNT(*) INTO nearby_count FROM zip_neighbors WHERE is_adjacent = false;
    SELECT AVG(distance_km), MAX(distance_km) INTO avg_distance, max_distance
    FROM zip_neighbors;

    RAISE NOTICE '   ✓ Created % neighbor relationships', total_neighbors;
    RAISE NOTICE '      - Adjacent (touching): %', adjacent_count;
    RAISE NOTICE '      - Nearby (within 10km): %', nearby_count;
    RAISE NOTICE '      - Avg distance: % km', ROUND(avg_distance, 2);
    RAISE NOTICE '      - Max distance: % km', ROUND(max_distance, 2);

    -- 数据质量警告
    IF EXISTS (SELECT 1 FROM zip_neighbors WHERE has_overlap = true) THEN
        RAISE WARNING '   ⚠️  Found overlapping ZIP codes (data quality issue)';
    END IF;
END $$;

\echo ''

-- ============================================================
-- Step 3: Census Tract → ZIP Crosswalk (如果有 census_tracts 表)
-- ============================================================
\echo '📊 Step 3: Computing Tract → ZIP crosswalk...'

DO $$
BEGIN
    -- 检查 census_tracts 表是否存在
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'census_tracts') THEN

        DROP TABLE IF EXISTS tract_zip_overlay CASCADE;

        CREATE TABLE tract_zip_overlay AS
        SELECT
            t.geoid AS tract_id,
            z.zip_code,

            -- 重叠面积和百分比
            ST_Area(ST_Intersection(t.geom, z.geom)::geography) / 1000000.0 AS overlap_area_km2,
            ST_Area(ST_Intersection(t.geom, z.geom)::geography) / ST_Area(t.geom::geography) * 100 AS overlap_pct_of_tract,
            ST_Area(ST_Intersection(t.geom, z.geom)::geography) / ST_Area(z.geom::geography) * 100 AS overlap_pct_of_zip,

            -- Centroid 是否在 ZIP 内
            ST_Contains(z.geom, ST_Centroid(t.geom)) AS tract_centroid_in_zip

        FROM census_tracts t
        JOIN zip_shapes z ON ST_Intersects(t.geom, z.geom)
        WHERE
            t.geom IS NOT NULL
            AND z.geom IS NOT NULL
            AND ST_Area(ST_Intersection(t.geom, z.geom)::geography) / ST_Area(t.geom::geography) > 0.05;  -- 5%+ overlap

        CREATE INDEX idx_tract_zip_tract ON tract_zip_overlay(tract_id);
        CREATE INDEX idx_tract_zip_zip ON tract_zip_overlay(zip_code);

        RAISE NOTICE '   ✓ Created tract → ZIP crosswalk';
        RAISE NOTICE '      - Total relationships: %', (SELECT COUNT(*) FROM tract_zip_overlay);

    ELSE
        RAISE NOTICE '   ⚠️  Table census_tracts not found, skipping...';
    END IF;
END $$;

\echo ''

-- ============================================================
-- Step 4: Building → ZIP Validation (如果有 buildings 或 housing_projects 表)
-- ============================================================
\echo '🏢 Step 4: Validating Building → ZIP assignments...'

DO $$
DECLARE
    has_buildings BOOLEAN;
    has_projects BOOLEAN;
BEGIN
    -- 检查 buildings 表
    SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'buildings')
    INTO has_buildings;

    -- 检查 housing_projects 表
    SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'housing_projects')
    INTO has_projects;

    -- 验证 housing_projects
    IF has_projects THEN
        DROP TABLE IF EXISTS project_zip_validation CASCADE;

        CREATE TABLE project_zip_validation AS
        SELECT
            p.project_id,
            p.project_name,
            p.zipcode AS reported_zip,
            z.zip_code AS actual_zip,
            ST_Contains(z.geom, p.geom) AS is_inside,
            ST_Distance(p.geom::geography, ST_Centroid(z.geom)::geography) / 1000.0 AS distance_to_centroid_km
        FROM housing_projects p
        LEFT JOIN zip_shapes z ON ST_Contains(z.geom, p.geom)
        WHERE p.geom IS NOT NULL;

        CREATE INDEX idx_project_validation_id ON project_zip_validation(project_id);

        DECLARE
            total_projects INTEGER;
            inside_count INTEGER;
            mismatch_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO total_projects FROM project_zip_validation;
            SELECT COUNT(*) INTO inside_count FROM project_zip_validation WHERE is_inside = true;
            SELECT COUNT(*) INTO mismatch_count
            FROM project_zip_validation
            WHERE reported_zip != actual_zip AND actual_zip IS NOT NULL;

            RAISE NOTICE '   ✓ Validated % housing projects', total_projects;
            RAISE NOTICE '      - Inside ZIP boundary: %', inside_count;
            RAISE NOTICE '      - ZIP mismatch: %', mismatch_count;

            IF mismatch_count > 0 THEN
                RAISE WARNING '   ⚠️  Found % projects with ZIP code mismatches', mismatch_count;
            END IF;
        END;
    ELSE
        RAISE NOTICE '   ⚠️  Table housing_projects not found, skipping validation...';
    END IF;

    -- 验证 buildings（如果数据量大，只抽样验证）
    IF has_buildings THEN
        DROP TABLE IF EXISTS building_zip_validation CASCADE;

        -- 如果 buildings 表很大，只验证前 10,000 条
        CREATE TABLE building_zip_validation AS
        SELECT
            b.building_id,
            b.zipcode AS reported_zip,
            z.zip_code AS actual_zip,
            ST_Contains(z.geom, b.geom) AS is_inside
        FROM (
            SELECT * FROM buildings
            WHERE geom IS NOT NULL
            LIMIT 10000
        ) b
        LEFT JOIN zip_shapes z ON ST_Contains(z.geom, b.geom);

        RAISE NOTICE '   ✓ Sampled building validation (first 10,000)';
    END IF;
END $$;

\echo ''

-- ============================================================
-- Summary Statistics
-- ============================================================
\echo '📈 Summary Statistics:'
\echo '========================================='

SELECT
    'ZIP Centroids' AS table_name,
    COUNT(*) AS row_count,
    pg_size_pretty(pg_total_relation_size('zip_centroids')) AS size
FROM zip_centroids
UNION ALL
SELECT
    'ZIP Neighbors',
    COUNT(*),
    pg_size_pretty(pg_total_relation_size('zip_neighbors'))
FROM zip_neighbors
UNION ALL
SELECT
    'Tract-ZIP Overlay',
    COALESCE((SELECT COUNT(*) FROM tract_zip_overlay), 0),
    COALESCE(pg_size_pretty(pg_total_relation_size('tract_zip_overlay')), 'N/A')
WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tract_zip_overlay')
UNION ALL
SELECT
    'Project Validation',
    COALESCE((SELECT COUNT(*) FROM project_zip_validation), 0),
    COALESCE(pg_size_pretty(pg_total_relation_size('project_zip_validation')), 'N/A')
WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'project_zip_validation');

\echo ''
\echo '✅ Spatial relationships precomputation complete!'
\echo ''
\echo 'Next steps:'
\echo '  1. Review the results in these tables:'
\echo '     - zip_centroids'
\echo '     - zip_neighbors'
\echo '     - tract_zip_overlay (if applicable)'
\echo '     - project_zip_validation (if applicable)'
\echo ''
\echo '  2. Run validation script:'
\echo '     python scripts/validate_spatial_precomputation.py'
\echo ''
\echo '  3. Visualize neighbor network:'
\echo '     jupyter notebook notebooks/02_visualize_zip_neighbors.ipynb'
\echo ''
