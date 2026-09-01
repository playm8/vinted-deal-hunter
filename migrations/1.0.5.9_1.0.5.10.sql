BEGIN TRANSACTION;

/* Vinted indexes an item in its search results long after the timestamp the
   item carries, so a short window silently drops every item. */
INSERT OR IGNORE INTO parameters (key, value)
VALUES ('item_max_age_minutes', '240');

UPDATE parameters
SET value = '1.0.5.10'
WHERE key = 'version';

COMMIT;
