BEGIN TRANSACTION;

/* Brands and sellers muted from a notification, so a bad match can be
   dismissed where it is seen instead of through the settings page. */
CREATE TABLE IF NOT EXISTS ignored_brands
(
    brand      TEXT PRIMARY KEY,
    ignored_at NUMERIC
);

CREATE TABLE IF NOT EXISTS ignored_sellers
(
    seller_id   TEXT PRIMARY KEY,
    seller_name TEXT,
    ignored_at  NUMERIC
);

/* The log has to carry what an action needs to act on. */
ALTER TABLE notification_log ADD COLUMN brand TEXT;
ALTER TABLE notification_log ADD COLUMN seller_id TEXT;
ALTER TABLE notification_log ADD COLUMN seller_name TEXT;

UPDATE parameters
SET value = '1.0.5.14'
WHERE key = 'version';

COMMIT;
