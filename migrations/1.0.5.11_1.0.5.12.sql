BEGIN TRANSACTION;

/* Observed indexing delay: how old the freshest item of a cycle was. Kept as
   a rolling window so the age filter can follow Vinted instead of guessing. */
CREATE TABLE IF NOT EXISTS indexing_delay_samples
(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    delay_minutes NUMERIC,
    observed_at  NUMERIC
);

CREATE INDEX IF NOT EXISTS idx_indexing_delay_observed
    ON indexing_delay_samples (observed_at);

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('item_max_age_mode', 'auto'),
       ('item_max_age_cap', '1440'),
       ('item_max_age_factor', '3'),
       ('item_max_age_effective', ''),
       ('indexing_delay_window', '60');

UPDATE parameters
SET value = '1.0.5.12'
WHERE key = 'version';

COMMIT;
