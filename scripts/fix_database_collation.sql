-- SQL script to convert database collation
-- Run this in MySQL Workbench or phpMyAdmin after importing

-- Convert entire database to utf8mb4_unicode_ci
ALTER DATABASE kemunca_website_Akmal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- If you need to convert specific tables:
-- ALTER TABLE your_table_name CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- To convert all tables in the database, run this for each table:
-- ALTER TABLE applicants CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- ALTER TABLE proposals CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- ALTER TABLE job_listings CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
