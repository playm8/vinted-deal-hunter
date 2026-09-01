BEGIN TRANSACTION;

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('backup_enabled', 'True'),
       ('backup_directory', './data/backups'),
       ('backup_keep', '7');

UPDATE parameters
SET value = '1.0.5.15'
WHERE key = 'version';

COMMIT;
