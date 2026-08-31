BEGIN TRANSACTION;

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('notify_silent_below', '25'),
       ('notify_skip_below', '');

UPDATE parameters
SET value = '1.0.5.6'
WHERE key = 'version';

COMMIT;
