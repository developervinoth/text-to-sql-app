
-- Additional Mock Tables Setup Script
-- Use this template to create mock tables for any additional real tables

-- Template for creating a mock table:
-- 1. Copy the structure of your real table
-- 2. Create {table_name}_sample with identical structure
-- 3. Insert 3-5 rows of safe, fictional data

-- Example for a new table called 'payments':
/*
CREATE TABLE payments_sample (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    payment_method TEXT,
    amount DECIMAL(10,2),
    payment_date TIMESTAMP,
    status TEXT
);

INSERT INTO payments_sample VALUES 
(1, 1, 'demo_card_****1234', 629.98, '2024-01-15 10:35:00', 'completed'),
(2, 2, 'demo_card_****5678', 1329.98, '2024-01-20 14:25:00', 'completed'),
(3, 3, 'demo_paypal', 219.98, '2024-02-01 09:20:00', 'pending');
*/

-- Guidelines for mock data:
-- [OK] Use fictional names, emails, addresses
-- [OK] Use demo/test/sample prefixes
-- [OK] Use safe card numbers (4111-1111-1111-1111 for testing)
-- [OK] Use realistic but fake amounts and dates
-- [NO] Never use real customer data
-- [NO] Never use real payment information
-- [NO] Never use real personal identifiers
