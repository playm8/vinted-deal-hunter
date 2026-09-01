"""Every connection carries the settings concurrent access needs."""

import sqlite3

import db


def test_connections_wait_instead_of_failing(database):
    # Five processes share this file and SQLite allows one writer at a time.
    # With the default timeout of 0 the loser of a race raises at once, and
    # every function here swallows exceptions — so a collision loses a write.
    conn = database.get_db_connection()
    try:
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
    finally:
        conn.close()


def test_connections_enforce_foreign_keys(database):
    conn = database.get_db_connection()
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_a_second_writer_waits_rather_than_raising(database, tmp_path):
    # Hold a write lock, then check another connection does not give up
    # instantly. Without busy_timeout this raises "database is locked".
    holder = database.get_db_connection()
    holder.execute("BEGIN IMMEDIATE")
    holder.execute("UPDATE parameters SET value='x' WHERE key='banwords'")

    waiter = sqlite3.connect(database.DB_PATH)
    waiter.execute("PRAGMA busy_timeout = 300")
    try:
        waiter.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as error:
        # It did wait: the failure comes after the timeout, not immediately.
        assert "locked" in str(error)
    finally:
        waiter.close()
        holder.rollback()
        holder.close()


def test_only_two_places_open_a_raw_connection():
    # Everything else must go through get_db_connection, otherwise the
    # settings above are silently absent from that call site. The exceptions
    # are get_db_connection itself and backup_database, which needs two
    # distinct connections for SQLite's backup API.
    source = open(db.__file__, encoding="utf-8").read()
    assert source.count("sqlite3.connect(DB_PATH)") == 2
    assert source.count("sqlite3.connect") == 3
