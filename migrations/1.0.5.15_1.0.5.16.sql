BEGIN TRANSACTION;

/* items carried no index at all, so is_item_in_db_by_id scanned the whole
   table for every item scraped, on every cycle, for every query.

   Deliberately not UNIQUE on items(item): the deduplication is global, so a
   unique index looks tempting, but it would turn any concurrent reinsert into
   an IntegrityError that add_item_to_db swallows silently. Non-unique gives
   the same read speed with no new failure mode. */
CREATE INDEX IF NOT EXISTS idx_items_item ON items (item);

/* get_items joins on query_id then sorts by timestamp, and
   remove_query_from_db deletes by query_id. One composite index serves both. */
CREATE INDEX IF NOT EXISTS idx_items_query_time ON items (query_id, timestamp DESC);

/* is_query_in_db and get_items look queries up by their URL. */
CREATE INDEX IF NOT EXISTS idx_queries_query ON queries (query);

UPDATE parameters
SET value = '1.0.5.16'
WHERE key = 'version';

COMMIT;
