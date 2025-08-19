
-- 1. Providers per city
SELECT city, COUNT(*) AS provider_count
FROM providers
GROUP BY city
ORDER BY provider_count DESC;

-- 2. Receivers per city
SELECT city, COUNT(*) AS receiver_count
FROM receivers
GROUP BY city
ORDER BY receiver_count DESC;

-- 3. Provider type contribution (total quantity)
SELECT fl.provider_type, SUM(fl.quantity) AS total_quantity
FROM food_listings fl
GROUP BY fl.provider_type
ORDER BY total_quantity DESC;

-- 4. Provider contacts in a specific city (parameterize city in app)
-- SELECT name, type, address, contact FROM providers WHERE city = ?;

-- 5. Receivers who claimed the most (by count of claims)
SELECT r.name AS receiver_name, COUNT(c.claim_id) AS total_claims
FROM claims c
JOIN receivers r ON c.receiver_id = r.receiver_id
GROUP BY r.name
ORDER BY total_claims DESC;

-- 6. Total quantity of food available
SELECT SUM(quantity) AS total_available_quantity FROM food_listings;

-- 7. City with highest number of food listings
SELECT location AS city, COUNT(*) AS listings
FROM food_listings
GROUP BY location
ORDER BY listings DESC;

-- 8. Most common food types
SELECT food_type, COUNT(*) AS cnt
FROM food_listings
GROUP BY food_type
ORDER BY cnt DESC;

-- 9. Claims per food item
SELECT fl.food_name, COUNT(c.claim_id) AS claims_count
FROM food_listings fl
LEFT JOIN claims c ON fl.food_id = c.food_id
GROUP BY fl.food_name
ORDER BY claims_count DESC;

-- 10. Provider with highest number of completed claims
SELECT p.name, COUNT(c.claim_id) AS completed_claims
FROM claims c
JOIN food_listings fl ON c.food_id = fl.food_id
JOIN providers p ON fl.provider_id = p.provider_id
WHERE LOWER(c.status) = 'completed'
GROUP BY p.name
ORDER BY completed_claims DESC;

-- 11. Claims status distribution
SELECT LOWER(status) AS status, COUNT(*) AS cnt
FROM claims
GROUP BY LOWER(status)
ORDER BY cnt DESC;

-- 12. Average quantity claimed per receiver (approximation: avg of quantities of foods they claimed)
SELECT r.name AS receiver_name, AVG(fl.quantity) AS avg_quantity_of_items_they_claimed
FROM claims c
JOIN receivers r ON c.receiver_id = r.receiver_id
JOIN food_listings fl ON c.food_id = fl.food_id
GROUP BY r.name
ORDER BY avg_quantity_of_items_they_claimed DESC;

-- 13. Most claimed meal type
SELECT fl.meal_type, COUNT(c.claim_id) AS claims_count
FROM claims c
JOIN food_listings fl ON c.food_id = fl.food_id
GROUP BY fl.meal_type
ORDER BY claims_count DESC;

-- 14. Total quantity donated by each provider
SELECT p.name, SUM(fl.quantity) AS total_donated
FROM food_listings fl
JOIN providers p ON fl.provider_id = p.provider_id
GROUP BY p.name
ORDER BY total_donated DESC;

-- 15. Listings nearing expiry (parameterized date window in app)
-- SELECT * FROM food_listings WHERE DATE(expiry_date) <= DATE('now', '+3 day');
