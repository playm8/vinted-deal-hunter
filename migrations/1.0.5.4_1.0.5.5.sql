BEGIN TRANSACTION;

/* Cache of market price references, keyed by locale/brand/keywords/size. */
CREATE TABLE IF NOT EXISTS price_reference_cache
(
    cache_key    TEXT PRIMARY KEY,
    median_price NUMERIC,
    currency     TEXT,
    sample_size  INTEGER,
    updated_at   NUMERIC
);

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('price_reference_enabled', 'True'),
       ('price_reference_sample_size', '20'),
       ('price_reference_min_samples', '5'),
       ('price_reference_ttl_hours', '24'),
       ('deal_threshold_good', '25'),
       ('deal_threshold_hot', '50');

/* Only upgrade the message template when it was left untouched. */
UPDATE parameters
SET value = '🆕 {title}
💶 {price}  (total {total_price})
📊 Market ref : {market_price}  ({discount})
{deal}
🛍️ {brand} · 📏 {size} · ✨ {status}
❤️ {favourites}  👁️ {views}
<a href="{image}">&#8205;</a>'
WHERE key = 'message_template'
  AND replace(value, char(13), '') = '🆕 Title : {title}
💶 Price : {price}
🛍️ Brand : {brand}
<a href="{image}">&#8205;</a>';

UPDATE parameters
SET value = '1.0.5.5'
WHERE key = 'version';

COMMIT;
