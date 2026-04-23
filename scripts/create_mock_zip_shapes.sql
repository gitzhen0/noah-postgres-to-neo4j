-- ============================================================
-- Create Mock ZIP Shapes for Testing
-- ============================================================
-- 目的：从现有的 housing_projects 点数据创建模拟的 ZIP polygon
-- 方法：使用 ST_ConvexHull 和 ST_Buffer 创建每个 ZIP 的边界
-- ============================================================

\echo '🗺️  Creating mock ZIP shapes from housing projects...'
\echo ''

-- ============================================================
-- Step 1: 为每个 ZIP 创建 convex hull（凸包）
-- ============================================================
\echo '📍 Step 1: Creating convex hulls for each ZIP...'

DROP TABLE IF EXISTS zip_shapes CASCADE;

CREATE TABLE zip_shapes AS
SELECT
    zipcode AS zip_code,

    -- 如果只有 1 个点，使用 buffer；否则使用 convex hull
    CASE
        WHEN COUNT(*) = 1 THEN
            -- 单个点：创建 500m 半径的圆形缓冲区
            ST_Buffer(ST_Collect(geom)::geography, 500)::geometry
        ELSE
            -- 多个点：创建凸包，然后扩展 200m
            ST_Buffer(
                ST_ConvexHull(ST_Collect(geom))::geography,
                200
            )::geometry
    END AS geom,

    -- 统计信息
    COUNT(*) AS num_projects,

    -- 项目的中心点（作为 ZIP centroid 的近似）
    ST_Centroid(ST_Collect(geom)) AS centroid

FROM housing_projects
WHERE geom IS NOT NULL AND zipcode IS NOT NULL
GROUP BY zipcode;

-- 设置正确的 SRID
UPDATE zip_shapes SET geom = ST_SetSRID(geom, 4326);

-- 添加索引
CREATE INDEX idx_zip_shapes_geom ON zip_shapes USING GIST(geom);
CREATE INDEX idx_zip_shapes_code ON zip_shapes(zip_code);

-- 验证
DO $$
DECLARE
    shape_count INTEGER;
    zip_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO shape_count FROM zip_shapes;
    SELECT COUNT(DISTINCT zipcode) INTO zip_count FROM housing_projects WHERE geom IS NOT NULL;

    RAISE NOTICE '   ✓ Created % ZIP shapes from % unique ZIPs', shape_count, zip_count;

    -- 显示一些统计
    RAISE NOTICE '   ✓ Area statistics:';
    RAISE NOTICE '      - Avg: % km²',
        (SELECT ROUND(AVG(ST_Area(geom::geography) / 1000000.0)::numeric, 2) FROM zip_shapes);
    RAISE NOTICE '      - Max: % km²',
        (SELECT ROUND(MAX(ST_Area(geom::geography) / 1000000.0)::numeric, 2) FROM zip_shapes);
    RAISE NOTICE '      - Min: % km²',
        (SELECT ROUND(MIN(ST_Area(geom::geography) / 1000000.0)::numeric, 2) FROM zip_shapes);
END $$;

\echo ''

-- ============================================================
-- Step 2: 为单项目 ZIP 创建更真实的形状
-- ============================================================
\echo '🔧 Step 2: Enhancing shapes for single-project ZIPs...'

-- 对于只有一个项目的 ZIP，创建一个更合理的正方形边界
UPDATE zip_shapes
SET geom = ST_Envelope(
    ST_Buffer(centroid::geography, 1000)::geometry  -- 1km x 1km 正方形
)
WHERE num_projects = 1;

DO $$ BEGIN RAISE NOTICE '   ✓ Enhanced shapes for single-project ZIPs'; END $$;

\echo ''

-- ============================================================
-- Step 3: 添加 borough 信息
-- ============================================================
\echo '🏙️  Step 3: Adding borough information...'

-- 添加 borough 列
ALTER TABLE zip_shapes ADD COLUMN borough VARCHAR(50);

-- 从 housing_projects 推断 borough（使用最常见的）
UPDATE zip_shapes z
SET borough = subq.most_common_borough
FROM (
    SELECT
        zipcode,
        MODE() WITHIN GROUP (ORDER BY borough) AS most_common_borough
    FROM housing_projects
    WHERE zipcode IS NOT NULL AND borough IS NOT NULL
    GROUP BY zipcode
) subq
WHERE z.zip_code = subq.zipcode;

DO $$ BEGIN RAISE NOTICE '   ✓ Added borough information'; END $$;

\echo ''

-- ============================================================
-- Step 4: 数据质量检查
-- ============================================================
\echo '🔍 Step 4: Data quality checks...'

DO $$
DECLARE
    null_geom_count INTEGER;
    invalid_geom_count INTEGER;
    overlapping_count INTEGER;
BEGIN
    -- 检查 NULL geometries
    SELECT COUNT(*) INTO null_geom_count FROM zip_shapes WHERE geom IS NULL;

    -- 检查无效 geometries
    SELECT COUNT(*) INTO invalid_geom_count FROM zip_shapes WHERE NOT ST_IsValid(geom);

    -- 检查重叠
    SELECT COUNT(*) INTO overlapping_count
    FROM zip_shapes a, zip_shapes b
    WHERE a.zip_code < b.zip_code
      AND ST_Overlaps(a.geom, b.geom);

    RAISE NOTICE '   Quality checks:';
    RAISE NOTICE '      - NULL geometries: %', null_geom_count;
    RAISE NOTICE '      - Invalid geometries: %', invalid_geom_count;
    RAISE NOTICE '      - Overlapping pairs: %', overlapping_count;

    IF null_geom_count > 0 OR invalid_geom_count > 0 THEN
        RAISE WARNING '   ⚠️  Found data quality issues!';
    ELSE
        RAISE NOTICE '   ✅ All geometries are valid!';
    END IF;
END $$;

\echo ''

-- ============================================================
-- Summary
-- ============================================================
\echo '📊 Mock ZIP Shapes Summary:'
\echo '========================================='

SELECT
    'Total ZIP shapes' AS metric,
    COUNT(*)::text AS value
FROM zip_shapes
UNION ALL
SELECT
    'With borough info',
    COUNT(*)::text
FROM zip_shapes WHERE borough IS NOT NULL
UNION ALL
SELECT
    'Avg area (km²)',
    ROUND(AVG(ST_Area(geom::geography) / 1000000.0)::numeric, 2)::text
FROM zip_shapes
UNION ALL
SELECT
    'Table size',
    pg_size_pretty(pg_total_relation_size('zip_shapes'))
FROM zip_shapes
LIMIT 1;

\echo ''
\echo '✅ Mock ZIP shapes created successfully!'
\echo ''
\echo '⚠️  Note: These are MOCK geometries created from project locations.'
\echo '   For production, use real NYC ZIP code boundaries.'
\echo ''
\echo 'Next step:'
\echo '  Run: psql -U postgres -h localhost -d noah_housing -f scripts/precompute_spatial_relationships.sql'
\echo '  Or:  docker exec -i noah-postgres psql -U postgres -d noah_housing < scripts/precompute_spatial_relationships.sql'
\echo ''
