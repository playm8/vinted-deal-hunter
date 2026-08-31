BEGIN TRANSACTION;

/* Past market references, kept to show how brand prices move over time. */
CREATE TABLE IF NOT EXISTS price_reference_history
(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    brand        TEXT,
    keywords     TEXT,
    median_price NUMERIC,
    currency     TEXT,
    sample_size  INTEGER,
    dispersion   NUMERIC,
    recorded_at  NUMERIC
);

CREATE INDEX IF NOT EXISTS idx_price_history_recorded
    ON price_reference_history (recorded_at);
CREATE INDEX IF NOT EXISTS idx_price_history_brand
    ON price_reference_history (brand);

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('price_history_retention_days', '90');

UPDATE parameters
SET value = '1.0.5.9'
WHERE key = 'version';

COMMIT;
