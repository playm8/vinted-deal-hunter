BEGIN TRANSACTION;

/* What actually happened to each item found, so the daily summary can report
   on it and a silent breakdown becomes visible. */
CREATE TABLE IF NOT EXISTS notification_log
(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id      NUMERIC,
    title        TEXT,
    price        NUMERIC,
    currency     TEXT,
    url          TEXT,
    discount_pct NUMERIC,
    deal         TEXT,
    silent       INTEGER DEFAULT 0,
    skipped      INTEGER DEFAULT 0,
    sent_at      NUMERIC
);

CREATE INDEX IF NOT EXISTS idx_notification_log_sent
    ON notification_log (sent_at);

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('watchdog_enabled', 'True'),
       ('watchdog_cycles', '30'),
       ('watchdog_empty_cycles', '0'),
       ('watchdog_alerted', 'False'),
       ('daily_summary_enabled', 'True'),
       ('daily_summary_hour', '20'),
       ('daily_summary_last_sent', ''),
       ('notification_log_retention_days', '30');

UPDATE parameters
SET value = '1.0.5.11'
WHERE key = 'version';

COMMIT;
