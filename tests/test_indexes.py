"""The indexes exist, and the queries actually use them."""


def plan(database, sql, params=()):
    """Return the query plan as one lowercase string."""
    conn = database.get_db_connection()
    try:
        rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    finally:
        conn.close()
    return " ".join(str(part) for row in rows for part in row).lower()


def test_looking_an_item_up_by_id_uses_an_index(database):
    # This runs for every item of every query on every cycle. Without an index
    # it is a full table scan, and the table only grows.
    steps = plan(database, "SELECT COUNT() FROM items WHERE item=?", (1,))
    assert "using index" in steps or "using covering index" in steps
    assert "scan items" not in steps


def test_listing_items_of_a_query_uses_an_index(database):
    steps = plan(
        database,
        "SELECT i.title FROM items i JOIN queries q ON i.query_id = q.id "
        "WHERE i.query_id=? ORDER BY i.timestamp DESC LIMIT 10",
        (1,),
    )
    assert "idx_items_query_time" in steps


def test_finding_a_query_by_url_uses_an_index(database):
    steps = plan(database, "SELECT id FROM queries WHERE query=?", ("https://x",))
    assert "using index" in steps or "using covering index" in steps


def test_the_item_index_is_not_unique(database):
    # A unique index would turn a concurrent reinsert into an IntegrityError
    # that add_item_to_db swallows, losing the item silently.
    conn = database.get_db_connection()
    try:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name='idx_items_item'"
        ).fetchone()
    finally:
        conn.close()
    assert row and "unique" not in row[0].lower()


def test_inserting_the_same_item_twice_still_works(database):
    # The behaviour the non-unique choice protects.
    for _ in range(2):
        database.add_item_to_db(
            id=1,
            title="Nike",
            query_id=1,
            price=10,
            timestamp=1,
            photo_url="https://x",
        )
