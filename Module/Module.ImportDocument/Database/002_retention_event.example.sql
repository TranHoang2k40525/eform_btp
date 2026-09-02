-- Optional operational example. Enable only after DBA approval and after file cleanup is coordinated.
-- This deletes database detail for terminal jobs after 30 days; application cleanup deletes physical files first.
-- SET GLOBAL event_scheduler = ON;
-- CREATE EVENT PurgeExpiredImportJobs
-- ON SCHEDULE EVERY 1 DAY
-- DO DELETE FROM ImportJob
--    WHERE ExpiresUtc < UTC_TIMESTAMP()
--      AND Status IN (90, 100, 110);

