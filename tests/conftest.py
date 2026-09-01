"""
Shared fixtures.

Every test runs against a real SQLite database built the way a fresh install
builds it: the initial schema, then every migration in version order. A test
therefore also proves the migration chain still applies cleanly.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core
import db  # noqa: E402

MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations"
)
INITIAL_SQL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "initial_db.sql"
)


# A fresh install starts at the version initial_db.sql writes; older ones may
# still enter the chain below that.
FRESH_INSTALL_VERSION = "1.0.3"
OLDEST_SUPPORTED_VERSION = "1.0.2"


def migration_chain(version=FRESH_INSTALL_VERSION):
    """Return the migration files in the order the application applies them."""
    available = os.listdir(MIGRATIONS_DIR)
    chain = []
    while True:
        nxt = next((f for f in available if f.startswith(version + "_")), None)
        if not nxt:
            return chain
        chain.append(nxt)
        version = nxt[: -len(".sql")].split("_")[1]


@pytest.fixture
def database(tmp_path, monkeypatch):
    """A migrated database, isolated per test."""
    path = str(tmp_path / "test.db")
    monkeypatch.setattr(db, "DB_PATH", path)
    db.create_or_update_sqlite_db(INITIAL_SQL)
    for migration in migration_chain():
        db.create_or_update_sqlite_db(os.path.join(MIGRATIONS_DIR, migration))
    # The scraper remembers the previous cycle's results in memory, so without
    # this a test would inherit whatever the last one left behind.
    core._previous_result_ids.clear()
    return db


class FakeItem:
    """An item with the fields the pipeline reads, without touching Vinted."""

    def __init__(self, **overrides):
        self.id = overrides.get("id", 1)
        self.title = overrides.get("title", "Nike Air Max 90")
        self.brand_title = overrides.get("brand", "Nike")
        self.size_title = overrides.get("size", "42")
        self.currency = overrides.get("currency", "EUR")
        self.price = overrides.get("price", "30.0")
        self.url = overrides.get("url", "https://www.vinted.fr/items/1-nike")
        self.photo = overrides.get("photo", "https://img/1.jpg")
        age = overrides.get("age_minutes", 5)
        self.created_at_ts = datetime.now(timezone.utc) - timedelta(minutes=age)
        self.raw_timestamp = int(self.created_at_ts.timestamp())
        self.seller_id = overrides.get("seller", "42")
        self.raw_data = {
            "user": {
                "id": self.seller_id,
                "login": overrides.get("seller_name", "bob"),
            },
            "status": overrides.get("status", "Très bon état"),
            "favourite_count": overrides.get("favourites", 3),
            "view_count": overrides.get("views", 7),
            "total_item_price": {"amount": overrides.get("total", "32.20")},
        }

    def is_new_item(self, minutes=240):
        """Mirrors Item.is_new_item so the pipeline can be exercised."""
        delta = datetime.now(timezone.utc) - self.created_at_ts
        return delta.total_seconds() < minutes * 60


@pytest.fixture
def item():
    return FakeItem
