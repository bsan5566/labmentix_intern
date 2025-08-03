
CREATE DATABASE IF NOT EXISTS uber_data;
USE uber_data;

-- Create table structure
CREATE TABLE uber_request_data (
    request_id INT,
    pickup_point VARCHAR(50),
    driver_id INT,
    status VARCHAR(50),
    request_timestamp VARCHAR(50),  
    drop_timestamp VARCHAR(50)     
);


-- View all data
SELECT * FROM uber_request_data;

-- Total requests by pickup point
SELECT pickup_point, COUNT(*) AS total_requests
FROM uber_request_data
GROUP BY pickup_point
ORDER BY total_requests DESC;

-- Percentage of each status
SELECT status,
       COUNT(*) AS total_requests,
       ROUND((COUNT(*) / (SELECT COUNT(*) FROM uber_request_data) * 100), 2) AS percentage
FROM uber_request_data
GROUP BY status;

-- Active drivers & total requests
SELECT COUNT(DISTINCT driver_id) AS active_drivers,
       COUNT(*) AS total_requests
FROM uber_request_data;

-- Show Excel serial date values & converted datetime
SELECT 
    request_timestamp AS excel_request_value,
    DATE_ADD('1899-12-30', INTERVAL request_timestamp DAY) AS request_datetime,
    drop_timestamp AS excel_drop_value,
    DATE_ADD('1899-12-30', INTERVAL drop_timestamp DAY) AS drop_datetime
FROM uber_request_data
LIMIT 50;

-- Cancellations by pickup point
SELECT pickup_point, COUNT(*) AS cancellations
FROM uber_request_data
WHERE status LIKE '%Cancelled%'
GROUP BY pickup_point
ORDER BY cancellations DESC;

--  Average trips per driver
SELECT ROUND(COUNT(*) / COUNT(DISTINCT driver_id), 2) AS avg_trips_per_driver
FROM uber_request_data
WHERE driver_id IS NOT NULL;

-- Daily total requests (Excel serial → date)
SELECT 
    DATE(DATE_ADD('1899-12-30', INTERVAL request_timestamp DAY)) AS request_date,
    COUNT(*) AS total_requests
FROM uber_request_data
GROUP BY request_date
ORDER BY request_date;
