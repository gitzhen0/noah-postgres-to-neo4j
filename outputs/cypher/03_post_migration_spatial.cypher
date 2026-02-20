// Post-Migration: Neo4j Point Properties & Spatial Indexes
// Run this AFTER data migration is complete
// Creates native Point type for spatial queries

MATCH (n:Zipcode)
WHERE n.center_lat IS NOT NULL AND n.center_lon IS NOT NULL
SET n.location = point({
    latitude: n.center_lat,
    longitude: n.center_lon,
    crs: 'WGS-84'
});

CREATE POINT INDEX zipcode_location IF NOT EXISTS
FOR (n:Zipcode)
ON (n.location);

MATCH (n:Building)
WHERE n.center_lat IS NOT NULL AND n.center_lon IS NOT NULL
SET n.location = point({
    latitude: n.center_lat,
    longitude: n.center_lon,
    crs: 'WGS-84'
});

CREATE POINT INDEX building_location IF NOT EXISTS
FOR (n:Building)
ON (n.location);

