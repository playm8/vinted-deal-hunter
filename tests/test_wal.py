"""Write-ahead logging, and why it is not set in a migration."""

import sqlite3


def test_the_database_ends_up_in_wal(database):
    conn = database.get_db_connection()
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    finally:
        conn.close()


def test_a_migration_could_not_have_done_this(tmp_path):
    # Every migration is wrapped in BEGIN/COMMIT and run through
    # executescript, and the pragma is refused inside a transaction. Putting it
    # in a migration raises and leaves the database in its previous mode — this
    # test records why the setting lives in get_db_connection instead.
    path = str(tmp_path / "m.db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (x)")
    conn.commit()
    try:
        conn.executescript("BEGIN TRANSACTION;\nPRAGMA journal_mode = WAL;\nCOMMIT;")
    except sqlite3.OperationalError as error:
        assert "wal" in str(error).lower()
    conn.close()
    assert (
        sqlite3.connect(path).execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    )


def test_readers_do_not_block_the_writer(database):
    # The point of WAL here: five processes share this file, and the web UI
    # reading must not stall the extractor writing.
    reader = database.get_db_connection()
    reader.execute("BEGIN")
    reader.execute("SELECT COUNT(*) FROM parameters").fetchone()

    writer = database.get_db_connection()
    try:
        writer.execute("UPDATE parameters SET value='x' WHERE key='banwords'")
        writer.commit()
    finally:
        writer.close()
        reader.rollback()
        reader.close()


def test_a_backup_taken_under_wal_is_readable(database, tmp_path):
    # Recent commits live in the -wal file, so copying the .db alone would
    # miss them. backup_database uses SQLite's backup API, which does not.
    database.set_parameter("banwords", "marker")
    path = database.backup_database(str(tmp_path / "bk"), keep_last=3)
    assert path
    value = (
        sqlite3.connect(path)
        .execute("SELECT value FROM parameters WHERE key='banwords'")
        .fetchone()
    )
    assert value[0] == "marker"


def test_checkpoint_is_harmless(database):
    database.checkpoint()
    assert database.get_parameter("version")
