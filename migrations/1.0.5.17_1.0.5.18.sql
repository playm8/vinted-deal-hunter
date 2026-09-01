BEGIN TRANSACTION;

/* Every stored sample was measured on items that were already in the previous
   cycle's results, so each one only records an item ageing rather than the
   indexing delay. On a quiet query that made the smallest sample climb by one
   minute per minute, and the age window with it, until it stuck at its cap
   and stopped filtering anything.

   The measurements are known wrong, and the rolling window would keep them
   for as long as it takes to gather that many correct ones -- now much longer,
   since a sample is only recorded when a genuinely new listing shows up.
   Fewer samples than MIN_DELAY_SAMPLES simply falls back to the configured
   floor, which is the safe direction. */
DELETE FROM indexing_delay_samples;

UPDATE parameters
SET value = '1.0.5.18'
WHERE key = 'version';

COMMIT;
