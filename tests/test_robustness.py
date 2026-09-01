"""Surviving a blocked request and a lost database."""

import os

from pyVintedVN.requester import backoff_delay


class FakeResponse:
    def __init__(self, headers=None):
        self.headers = headers or {}


def test_delay_grows_with_each_attempt():
    delays = [backoff_delay(n) for n in range(1, 5)]
    assert delays == [1.0, 2.0, 4.0, 8.0]


def test_delay_never_exceeds_the_cap():
    assert backoff_delay(20) == 60.0
    assert backoff_delay(20, cap=5) == 5.0


def test_retry_after_is_obeyed_when_vinted_sends_one():
    # When the server says how long to wait, arguing with it is how a
    # temporary block becomes a lasting one.
    assert backoff_delay(1, FakeResponse({"Retry-After": "30"})) == 30.0


def test_an_unusable_retry_after_falls_back_to_the_delay():
    assert backoff_delay(3, FakeResponse({"Retry-After": "soon"})) == 4.0


def test_retry_after_is_still_capped():
    assert backoff_delay(1, FakeResponse({"Retry-After": "9999"})) == 60.0


def test_backup_produces_a_usable_database(database, tmp_path):
    database.set_parameter("banwords", "marker-value")
    path = database.backup_database(str(tmp_path / "backups"), keep_last=7)
    assert path and os.path.exists(path)

    import sqlite3

    value = (
        sqlite3.connect(path)
        .execute("SELECT value FROM parameters WHERE key='banwords'")
        .fetchone()
    )
    assert value[0] == "marker-value"


def test_backup_keeps_only_the_last_few(database, tmp_path):
    directory = str(tmp_path / "backups")
    for index in range(5):
        # Same second, so the rotation cannot rely on timestamps being unique.
        path = database.backup_database(directory, keep_last=3)
        assert path
        os.rename(path, os.path.join(directory, f"vinted_notifications-{index:03}.db"))
    database.backup_database(directory, keep_last=3)
    assert len(os.listdir(directory)) == 3


def test_backup_failure_is_reported_not_raised(database, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", "/nonexistent/path/to.db")
    assert database.backup_database("/proc/cannot-write-here", keep_last=1) is None
