import os
import sqlite3
from time import strftime, time
from traceback import print_exc

DB_PATH = "./data/vinted_notifications.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_or_update_sqlite_db(db_path):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Using the sql script
        with open(db_path, encoding="utf-8") as sql_file:
            sql_script = sql_file.read()
            cursor.executescript(sql_script)

        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def is_item_in_db_by_id(id):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT() FROM items WHERE item=?", (id,))
        if cursor.fetchone()[0]:
            return True
        return False
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def get_last_timestamp(query_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT last_item FROM queries WHERE id=?", (query_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    except Exception:
        print_exc()
        return None
    finally:
        if conn:
            conn.close()


def update_last_timestamp(query_id, timestamp):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE queries SET last_item=? WHERE id=?", (timestamp, query_id)
        )
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def add_item_to_db(id, title, query_id, price, timestamp, photo_url, currency="EUR"):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert into db the id and the query_id related to the item
        cursor.execute(
            "INSERT INTO items (item, title, price, currency, timestamp, photo_url, query_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id, title, price, currency, timestamp, photo_url, query_id),
        )
        # Update the last item for the query
        cursor.execute(
            "UPDATE queries SET last_item=? WHERE id=?", (timestamp, query_id)
        )
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def get_queries():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, query, last_item, query_name FROM queries")
        return cursor.fetchall()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def get_query_url(query_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT query FROM queries WHERE id=?", (query_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception:
        print_exc()
        return None
    finally:
        if conn:
            conn.close()


def is_query_in_db(processed_query):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # replace spaces in searched_text by % to match any query containing the searched text

        cursor.execute(
            "SELECT COUNT() FROM queries WHERE query = ?", (processed_query,)
        )
        if cursor.fetchone()[0]:
            return True
        return False
    except Exception:
        print_exc()
        return False
    finally:
        if conn:
            conn.close()


def add_query_to_db(query, name=None):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if name:
            cursor.execute(
                "INSERT INTO queries (query, last_item, query_name) VALUES (?, NULL, ?)",
                (query, name),
            )
        else:
            cursor.execute(
                "INSERT INTO queries (query, last_item) VALUES (?, NULL)", (query,)
            )
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def get_query_id_by_rowid(rowid):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = f"SELECT id FROM (SELECT id, ROW_NUMBER() OVER (ORDER BY ROWID) rn FROM queries) t WHERE rn={rowid}"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    except Exception:
        print_exc()
        return None
    finally:
        if conn:
            conn.close()


def remove_query_from_db(query_number):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Delete items associated with this query using query_id
        cursor.execute("DELETE FROM items WHERE query_id=?", (query_number,))
        # Delete the query
        cursor.execute("DELETE FROM queries WHERE id=?", (query_number,))
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def remove_all_queries_from_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Delete all items first to maintain foreign key integrity
        cursor.execute("DELETE FROM items")
        # Then delete all queries
        cursor.execute("DELETE FROM queries")
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def update_query_in_db(query_id, query, name):
    """
    Update an existing query in the database.

    Args:
        query_id (int): The ID of the query to update
        query (str): The new query URL
        name (str, optional): The new name for the query

    Returns:
        bool: True if the query was updated successfully, False otherwise
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE queries SET query=?, query_name=? WHERE id=?",
            (query, name, query_id),
        )
        conn.commit()
        return True
    except Exception:
        print_exc()
        return False
    finally:
        if conn:
            conn.close()


def add_to_allowlist(country):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO allowlist VALUES (?)", (country,))
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def remove_from_allowlist(country):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM allowlist WHERE country=?", (country,))
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def get_allowlist():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM allowlist")
        # Get list of countries
        countries = [country[0] for country in cursor.fetchall()]
        # Return 0 if there are no countries in the allowlist
        if not countries:
            return 0
        return countries
    finally:
        if conn:
            conn.close()


def clear_allowlist():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM allowlist")
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


# Settings that are credentials rather than preferences. Each can be supplied
# through the environment, which keeps it out of the database and therefore out
# of the web interface, backups and any accidental commit.
SECRET_PARAMETERS = {
    "telegram_token": "TELEGRAM_TOKEN",
    "telegram_chat_id": "TELEGRAM_CHAT_ID",
    "proxy_list": "PROXY_LIST",
}


def secret_is_from_env(key):
    """Return True when the environment supplies this setting."""
    variable = SECRET_PARAMETERS.get(key)
    return bool(variable and os.environ.get(variable))


def get_secret(key):
    """
    Read a credential, preferring the environment over the database.

    Args:
        key (str): The parameter name.

    Returns:
        str | None: The value, from the environment when it defines one.
    """
    variable = SECRET_PARAMETERS.get(key)
    if variable:
        value = os.environ.get(variable)
        if value:
            return value
    return get_parameter(key)


def get_parameter(key):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM parameters WHERE key=?", (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def set_parameter(key, value):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE parameters SET value=? WHERE key=?", (value, key))
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def get_all_parameters():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM parameters")
        return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception:
        print_exc()
        return {}
    finally:
        if conn:
            conn.close()


def get_items(limit=50, query=None):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if query:
            # Get the query_id for the given query
            cursor.execute("SELECT id FROM queries WHERE query=?", (query,))
            result = cursor.fetchone()
            if result:
                query_id = result[0]
                # Get items with the matching query_id
                cursor.execute(
                    "SELECT i.item, i.title, i.price, i.currency, i.timestamp, q.query, i.photo_url, q.query_name FROM items i JOIN queries q ON i.query_id = q.id WHERE i.query_id=? ORDER BY i.timestamp DESC LIMIT ?",
                    (query_id, limit),
                )
            else:
                return []
        else:
            # Join with queries table to get the query text
            cursor.execute(
                "SELECT i.item, i.title, i.price, i.currency, i.timestamp, q.query, i.photo_url, q.query_name FROM items i JOIN queries q ON i.query_id = q.id ORDER BY i.timestamp DESC LIMIT ?",
                (limit,),
            )
        return cursor.fetchall()
    except Exception:
        print_exc()
        return []
    finally:
        if conn:
            conn.close()


def get_total_items_count():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM items")
        return cursor.fetchone()[0]
    except Exception:
        print_exc()
        return 0
    finally:
        if conn:
            conn.close()


def get_total_queries_count():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM queries")
        return cursor.fetchone()[0]
    except Exception:
        print_exc()
        return 0
    finally:
        if conn:
            conn.close()


def get_last_found_item():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT i.item, i.title, i.price, i.currency, i.timestamp, q.query, i.photo_url FROM items i JOIN queries q ON i.query_id = q.id ORDER BY i.timestamp DESC LIMIT 1"
        )
        return cursor.fetchone()
    except Exception:
        print_exc()
        return None
    finally:
        if conn:
            conn.close()


def get_items_per_day():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get total items
        cursor.execute("SELECT COUNT(*) FROM items")
        total_items = cursor.fetchone()[0]

        if total_items == 0:
            return 0

        # Get earliest and latest timestamps
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM items")
        min_timestamp, max_timestamp = cursor.fetchone()

        # Calculate number of days (add 1 to include both start and end days)
        import datetime

        min_date = datetime.datetime.fromtimestamp(min_timestamp).date()
        max_date = datetime.datetime.fromtimestamp(max_timestamp).date()
        days_diff = (max_date - min_date).days + 1

        # Ensure at least 1 day to avoid division by zero
        days_diff = max(1, days_diff)

        # Calculate items per day
        return round(total_items / days_diff, 1)
    except Exception:
        print_exc()
        return 0
    finally:
        if conn:
            conn.close()


def get_price_reference(cache_key, max_age_seconds):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT median_price, currency, sample_size, updated_at, "
            "dispersion, condition_matched "
            "FROM price_reference_cache WHERE cache_key=?",
            (cache_key,),
        )
        result = cursor.fetchone()
        if result is None:
            return None
        if time() - result[3] > max_age_seconds:
            return None
        return {
            "median": result[0],
            "currency": result[1],
            "sample_size": result[2],
            "dispersion": result[4],
            "condition_matched": bool(result[5]),
        }
    except Exception:
        print_exc()
        return None
    finally:
        if conn:
            conn.close()


def set_price_reference(
    cache_key,
    median_price,
    currency,
    sample_size,
    dispersion=0,
    condition_matched=False,
):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO price_reference_cache "
            "(cache_key, median_price, currency, sample_size, updated_at, "
            "dispersion, condition_matched) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(cache_key) DO UPDATE SET "
            "median_price=excluded.median_price, currency=excluded.currency, "
            "sample_size=excluded.sample_size, updated_at=excluded.updated_at, "
            "dispersion=excluded.dispersion, "
            "condition_matched=excluded.condition_matched",
            (
                cache_key,
                median_price,
                currency,
                sample_size,
                time(),
                dispersion,
                int(condition_matched),
            ),
        )
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def add_price_reference_history(
    brand, keywords, median_price, currency, sample_size, dispersion
):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO price_reference_history "
            "(brand, keywords, median_price, currency, sample_size, "
            "dispersion, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (brand, keywords, median_price, currency, sample_size, dispersion, time()),
        )
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def purge_price_reference_history(max_age_days):
    """Drop history older than the retention window, keeping the table small."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM price_reference_history WHERE recorded_at < ?",
            (time() - max_age_days * 86400,),
        )
        conn.commit()
        return cursor.rowcount
    except Exception:
        print_exc()
        return 0
    finally:
        if conn:
            conn.close()


def get_price_trends(days=30, limit=20):
    """
    Summarise how brand price references moved over a period.

    Returns one row per brand with its oldest and newest median, so a caller
    can show whether a brand is getting cheaper or more expensive.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT brand,
                   COUNT(*) AS samples,
                   ROUND(AVG(median_price), 2) AS average_median,
                   ROUND(MIN(median_price), 2) AS lowest,
                   ROUND(MAX(median_price), 2) AS highest,
                   MAX(currency) AS currency
            FROM price_reference_history
            WHERE recorded_at >= ? AND brand IS NOT NULL AND brand != ''
            GROUP BY brand
            HAVING samples >= 2
            ORDER BY samples DESC
            LIMIT ?
            """,
            (time() - days * 86400, limit),
        )
        return cursor.fetchall()
    except Exception:
        print_exc()
        return []
    finally:
        if conn:
            conn.close()


def add_notification_log(
    item_id,
    title,
    price,
    currency,
    url,
    discount_pct,
    deal,
    silent,
    skipped,
    brand=None,
    seller_id=None,
    seller_name=None,
):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notification_log (item_id, title, price, currency, "
            "url, discount_pct, deal, silent, skipped, sent_at, brand, "
            "seller_id, seller_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item_id,
                title,
                price,
                currency,
                url,
                discount_pct,
                deal,
                int(silent),
                int(skipped),
                time(),
                brand,
                seller_id,
                seller_name,
            ),
        )
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def get_notification_summary(since_timestamp):
    """
    Summarise what happened to the items found since a point in time.

    Returns:
        dict: counts of items seen, notified, silenced and skipped, plus the
            best deal of the period as a row or None.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*), "
            "SUM(CASE WHEN skipped = 0 THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN skipped = 0 AND silent = 1 THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN skipped = 1 THEN 1 ELSE 0 END) "
            "FROM notification_log WHERE sent_at >= ?",
            (since_timestamp,),
        )
        seen, notified, silenced, skipped = cursor.fetchone()
        cursor.execute(
            "SELECT title, price, currency, url, discount_pct FROM notification_log "
            "WHERE sent_at >= ? AND skipped = 0 AND discount_pct IS NOT NULL "
            "ORDER BY discount_pct DESC LIMIT 1",
            (since_timestamp,),
        )
        return {
            "seen": seen or 0,
            "notified": notified or 0,
            "silenced": silenced or 0,
            "skipped": skipped or 0,
            "best": cursor.fetchone(),
        }
    except Exception:
        print_exc()
        return {"seen": 0, "notified": 0, "silenced": 0, "skipped": 0, "best": None}
    finally:
        if conn:
            conn.close()


def purge_notification_log(max_age_days):
    """Drop notification history older than the retention window."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM notification_log WHERE sent_at < ?",
            (time() - max_age_days * 86400,),
        )
        conn.commit()
        return cursor.rowcount
    except Exception:
        print_exc()
        return 0
    finally:
        if conn:
            conn.close()


def add_indexing_delay_sample(delay_minutes, keep_last):
    """
    Record how old the freshest item of a cycle was, keeping a rolling window.

    Args:
        delay_minutes (float): Age of the freshest item returned.
        keep_last (int): How many samples to retain.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO indexing_delay_samples (delay_minutes, observed_at) "
            "VALUES (?, ?)",
            (delay_minutes, time()),
        )
        cursor.execute(
            "DELETE FROM indexing_delay_samples WHERE id NOT IN "
            "(SELECT id FROM indexing_delay_samples ORDER BY id DESC LIMIT ?)",
            (keep_last,),
        )
        conn.commit()
    except Exception:
        print_exc()
    finally:
        if conn:
            conn.close()


def get_indexing_delay_samples():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT delay_minutes FROM indexing_delay_samples")
        return [row[0] for row in cursor.fetchall() if row[0] is not None]
    except Exception:
        print_exc()
        return []
    finally:
        if conn:
            conn.close()


def ignore_brand(brand):
    """Mute a brand. Returns False when it was already muted."""
    return _add_to_ignore_list(
        "INSERT INTO ignored_brands (brand, ignored_at) VALUES (?, ?)",
        (brand, time()),
    )


def ignore_seller(seller_id, seller_name):
    """Mute a seller. Returns False when they were already muted."""
    return _add_to_ignore_list(
        "INSERT INTO ignored_sellers (seller_id, seller_name, ignored_at) "
        "VALUES (?, ?, ?)",
        (str(seller_id), seller_name, time()),
    )


def _add_to_ignore_list(statement, values):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(statement, values)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception:
        print_exc()
        return False
    finally:
        if conn:
            conn.close()


def get_ignored_brands():
    return _fetch_column("SELECT brand FROM ignored_brands")


def get_ignored_sellers():
    return _fetch_column("SELECT seller_id FROM ignored_sellers")


def _fetch_column(query):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        return [str(row[0]) for row in conn.execute(query)]
    except Exception:
        print_exc()
        return []
    finally:
        if conn:
            conn.close()


def unignore_brand(brand):
    return _delete_one("DELETE FROM ignored_brands WHERE brand=?", (brand,))


def unignore_seller(seller_id):
    return _delete_one(
        "DELETE FROM ignored_sellers WHERE seller_id=?", (str(seller_id),)
    )


def _delete_one(statement, values):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(statement, values)
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        print_exc()
        return False
    finally:
        if conn:
            conn.close()


def get_ignored_lists():
    """Return muted brands and sellers for display, newest first."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        return {
            "brands": conn.execute(
                "SELECT brand, ignored_at FROM ignored_brands ORDER BY ignored_at DESC"
            ).fetchall(),
            "sellers": conn.execute(
                "SELECT seller_id, seller_name, ignored_at FROM ignored_sellers "
                "ORDER BY ignored_at DESC"
            ).fetchall(),
        }
    except Exception:
        print_exc()
        return {"brands": [], "sellers": []}
    finally:
        if conn:
            conn.close()


def get_logged_item(item_id):
    """Look up what was notified for an item, to act on it later."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT title, brand, seller_id, seller_name FROM notification_log "
            "WHERE item_id=? ORDER BY id DESC LIMIT 1",
            (item_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "title": row[0],
            "brand": row[1],
            "seller_id": row[2],
            "seller_name": row[3],
        }
    except Exception:
        print_exc()
        return None
    finally:
        if conn:
            conn.close()


def backup_database(directory, keep_last):
    """
    Write a consistent copy of the database, keeping the last few.

    SQLite's own backup API is used rather than copying the file, so a backup
    taken while the application is writing is still a valid database.

    Args:
        directory (str): Where to write backups.
        keep_last (int): How many backups to retain.

    Returns:
        str | None: The path written, or None on failure.
    """
    source = None
    target = None
    try:
        os.makedirs(directory, exist_ok=True)
        stamp = strftime("%Y%m%d-%H%M%S")
        path = os.path.join(directory, f"vinted_notifications-{stamp}.db")
        source = sqlite3.connect(DB_PATH)
        target = sqlite3.connect(path)
        source.backup(target)
        target.close()
        target = None

        backups = sorted(
            f
            for f in os.listdir(directory)
            if f.startswith("vinted_notifications-") and f.endswith(".db")
        )
        for stale in backups[: max(len(backups) - keep_last, 0)]:
            try:
                os.remove(os.path.join(directory, stale))
            except OSError:
                pass
        return path
    except Exception:
        print_exc()
        return None
    finally:
        if source:
            source.close()
        if target:
            target.close()


def get_price_history_series(days=30, limit=6):
    """
    Return a daily median per brand, for drawing a trend line.

    Only brands with enough distinct days are returned, since two points do
    not make a trend.

    Args:
        days (int): How far back to look.
        limit (int): How many brands to return.

    Returns:
        list[tuple]: (brand, [(day, median), ...]) newest last.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            """
            SELECT brand,
                   date(recorded_at, 'unixepoch') AS day,
                   ROUND(AVG(median_price), 2)
            FROM price_reference_history
            WHERE recorded_at >= ? AND brand IS NOT NULL AND brand != ''
            GROUP BY brand, day
            ORDER BY brand, day
            """,
            (time() - days * 86400,),
        ).fetchall()
        series = {}
        for brand, day, median in rows:
            series.setdefault(brand, []).append((day, median))
        usable = [(b, p) for b, p in series.items() if len(p) >= 2]
        usable.sort(key=lambda item: len(item[1]), reverse=True)
        return usable[:limit]
    except Exception:
        print_exc()
        return []
    finally:
        if conn:
            conn.close()
