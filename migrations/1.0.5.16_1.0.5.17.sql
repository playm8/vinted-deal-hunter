BEGIN TRANSACTION;

/* Price history per item, so a listing that gets cheaper can be recognised.
   Until now an item was notified once and never looked at again. */
ALTER TABLE items ADD COLUMN first_price NUMERIC;
ALTER TABLE items ADD COLUMN last_price NUMERIC;
ALTER TABLE items ADD COLUMN last_seen NUMERIC;

/* The price a drop is measured against. It only moves down when a drop is
   announced, so a seller nudging the price cannot alert on every cycle. */
ALTER TABLE items ADD COLUMN drop_baseline_price NUMERIC;
ALTER TABLE items ADD COLUMN drop_notified_at NUMERIC;

/* Existing rows need a baseline, otherwise they can never report a drop:
   safe, but silently useless for as long as they stay in the table. */
UPDATE items
SET first_price = price,
    last_price = price,
    drop_baseline_price = price;

/* Tells a price drop apart from a first sighting in the daily summary. */
ALTER TABLE notification_log ADD COLUMN kind TEXT DEFAULT 'new';

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('price_drop_enabled', 'True'),
       ('price_drop_min_pct', '10'),
       ('price_drop_min_amount', '3'),
       ('price_drop_cooldown_hours', '24'),
       ('price_drop_max_per_cycle', '5');

UPDATE parameters
SET value = '1.0.5.17'
WHERE key = 'version';

COMMIT;
