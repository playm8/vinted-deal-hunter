BEGIN TRANSACTION;

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('ui_language', 'en');

UPDATE parameters
SET value = '1.0.5.7'
WHERE key = 'version';

COMMIT;
