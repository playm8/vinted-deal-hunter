BEGIN TRANSACTION;

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('web_ui_auth_warning', 'True');

UPDATE parameters
SET value = '1.0.5.13'
WHERE key = 'version';

COMMIT;
