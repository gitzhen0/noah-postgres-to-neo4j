-- Sample Data for NOAH MVP Testing
-- ~20 housing projects across 3 boroughs and ~5 ZIP codes
-- This provides enough data to test relationships and conversions

-- Sample Housing Projects
INSERT INTO housing_projects (project_id, project_name, borough, zipcode, street_address, latitude, longitude, completion_date, total_units, affordable_units) VALUES
-- Manhattan Projects
('PROJ-MAN-001', 'Affordable Housing Complex A', 'Manhattan', '10001', '123 W 34th St', 40.7506, -73.9935, '2020-06-15', 150, 120),
('PROJ-MAN-002', 'Hudson Yards Affordable', 'Manhattan', '10001', '456 W 30th St', 40.7549, -74.0020, '2021-03-22', 200, 180),
('PROJ-MAN-003', 'Lower East Side Housing', 'Manhattan', '10002', '789 Delancey St', 40.7180, -73.9877, '2019-11-10', 80, 70),
('PROJ-MAN-004', 'East Village Residences', 'Manhattan', '10003', '321 E 9th St', 40.7295, -73.9865, '2022-01-05', 120, 100),
('PROJ-MAN-005', 'Chelsea Affordable Units', 'Manhattan', '10001', '555 W 23rd St', 40.7469, -74.0029, '2020-09-18', 90, 85),
('PROJ-MAN-006', 'Chinatown Community Housing', 'Manhattan', '10002', '100 Mott St', 40.7162, -73.9988, '2021-07-30', 65, 60),

-- Brooklyn Projects
('PROJ-BRK-001', 'Williamsburg Commons', 'Brooklyn', '11211', '200 Bedford Ave', 40.7144, -73.9580, '2020-05-12', 180, 150),
('PROJ-BRK-002', 'DUMBO Affordable Living', 'Brooklyn', '11201', '75 Washington St', 40.7033, -73.9888, '2021-12-01', 110, 95),
('PROJ-BRK-003', 'Park Slope Family Housing', 'Brooklyn', '11215', '450 7th Ave', 40.6631, -73.9823, '2019-08-20', 95, 85),
('PROJ-BRK-004', 'Bushwick Residences', 'Brooklyn', '11221', '888 Broadway', 40.6897, -73.9196, '2022-04-15', 130, 110),
('PROJ-BRK-005', 'Crown Heights Commons', 'Brooklyn', '11225', '600 Franklin Ave', 40.6708, -73.9559, '2020-10-25', 75, 70),
('PROJ-BRK-006', 'Sunset Park Towers', 'Brooklyn', '11220', '5000 4th Ave', 40.6432, -74.0102, '2021-06-08', 160, 140),

-- Bronx Projects
('PROJ-BRX-001', 'Fordham Plaza Housing', 'Bronx', '10458', '300 E Fordham Rd', 40.8622, -73.8887, '2020-02-28', 140, 120),
('PROJ-BRX-002', 'Concourse Village', 'Bronx', '10451', '500 E 161st St', 40.8282, -73.9221, '2021-09-14', 105, 90),
('PROJ-BRX-003', 'Melrose Commons', 'Bronx', '10451', '700 Melrose Ave', 40.8223, -73.9159, '2019-12-05', 85, 75),
('PROJ-BRX-004', 'Tremont Residences', 'Bronx', '10457', '1200 Grand Concourse', 40.8485, -73.9019, '2022-03-10', 95, 85),
('PROJ-BRX-005', 'Morris Heights Housing', 'Bronx', '10453', '1500 Jerome Ave', 40.8507, -73.9175, '2020-11-20', 110, 100),
('PROJ-BRX-006', 'Kingsbridge Affordable', 'Bronx', '10463', '3800 Sedgwick Ave', 40.8772, -73.9011, '2021-05-17', 125, 110),

-- Queens Projects (bonus)
('PROJ-QNS-001', 'Astoria Greens', 'Queens', '11106', '25-10 Astoria Blvd', 40.7716, -73.9255, '2020-07-22', 145, 130),
('PROJ-QNS-002', 'Long Island City Commons', 'Queens', '11101', '11-11 Queens Plaza', 40.7503, -73.9383, '2021-10-05', 170, 155);

-- Update ZIP Summary (aggregate from housing_projects)
INSERT INTO zip_summary (zipcode, borough, total_projects, total_units, total_affordable_units, avg_units_per_project, center_lat, center_lon)
SELECT
    zipcode,
    borough,
    COUNT(*) as total_projects,
    SUM(total_units) as total_units,
    SUM(affordable_units) as total_affordable_units,
    AVG(total_units) as avg_units_per_project,
    AVG(latitude) as center_lat,
    AVG(longitude) as center_lon
FROM housing_projects
WHERE zipcode IS NOT NULL
GROUP BY zipcode, borough
ON CONFLICT (zipcode) DO UPDATE SET
    borough = EXCLUDED.borough,
    total_projects = EXCLUDED.total_projects,
    total_units = EXCLUDED.total_units,
    total_affordable_units = EXCLUDED.total_affordable_units,
    avg_units_per_project = EXCLUDED.avg_units_per_project,
    center_lat = EXCLUDED.center_lat,
    center_lon = EXCLUDED.center_lon,
    last_updated = CURRENT_TIMESTAMP;

-- Update Borough Summary
INSERT INTO borough_summary (borough, total_zipcodes, total_projects, total_units, total_affordable_units)
SELECT
    borough,
    COUNT(DISTINCT zipcode) as total_zipcodes,
    SUM(total_projects) as total_projects,
    SUM(total_units) as total_units,
    SUM(total_affordable_units) as total_affordable_units
FROM zip_summary
GROUP BY borough
ON CONFLICT (borough) DO UPDATE SET
    total_zipcodes = EXCLUDED.total_zipcodes,
    total_projects = EXCLUDED.total_projects,
    total_units = EXCLUDED.total_units,
    total_affordable_units = EXCLUDED.total_affordable_units,
    last_updated = CURRENT_TIMESTAMP;

-- Verify data loaded
SELECT 'Data Load Summary:' as status;
SELECT 'Housing Projects:', COUNT(*) FROM housing_projects;
SELECT 'ZIP Codes:', COUNT(*) FROM zip_summary;
SELECT 'Boroughs:', COUNT(*) FROM borough_summary;
SELECT * FROM project_stats;
