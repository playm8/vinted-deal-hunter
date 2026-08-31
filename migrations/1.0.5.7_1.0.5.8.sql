BEGIN TRANSACTION;

ALTER TABLE price_reference_cache ADD COLUMN dispersion NUMERIC DEFAULT 0;
ALTER TABLE price_reference_cache ADD COLUMN condition_matched INTEGER DEFAULT 0;

/* Cached references predate the quality columns and the condition-aware key. */
DELETE FROM price_reference_cache;

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('price_reference_max_dispersion', '80');

UPDATE parameters
SET value = '1.0.5.8'
WHERE key = 'version';

COMMIT;
