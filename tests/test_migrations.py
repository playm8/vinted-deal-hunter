"""The migration chain and the settings it is expected to create."""

import conftest


def test_every_migration_is_reachable():
    import os

    # Walked from the oldest supported version, since a fresh install starts
    # later than that. A migration nobody can reach would never run at all.
    chain = conftest.migration_chain(conftest.OLDEST_SUPPORTED_VERSION)
    on_disk = [f for f in os.listdir(conftest.MIGRATIONS_DIR) if f.endswith(".sql")]
    assert set(chain) == set(on_disk), sorted(set(on_disk) - set(chain))


def test_a_fresh_install_starts_where_the_schema_leaves_it(database):
    # initial_db.sql already writes a version, so the migrations before it are
    # only there for installs upgrading from further back.
    assert conftest.migration_chain()[0].startswith(conftest.FRESH_INSTALL_VERSION)


def test_chain_lands_on_the_current_version(database):
    last = conftest.migration_chain()[-1]
    expected = last[: -len(".sql")].split("_")[1]
    assert database.get_parameter("version") == expected


def test_settings_the_pipeline_relies_on_exist(database):
    for key in (
        "message_template",
        "item_max_age_minutes",
        "item_max_age_mode",
        "item_max_age_cap",
        "price_reference_enabled",
        "price_reference_min_samples",
        "price_reference_max_dispersion",
        "notify_silent_below",
        "notify_skip_below",
        "watchdog_enabled",
        "watchdog_cycles",
        "daily_summary_enabled",
        "ui_language",
    ):
        assert database.get_parameter(key) is not None, key


def test_tables_the_pipeline_relies_on_exist(database):
    import sqlite3

    names = {
        row[0]
        for row in sqlite3.connect(database.DB_PATH).execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert {
        "queries",
        "items",
        "parameters",
        "price_reference_cache",
        "price_reference_history",
        "notification_log",
        "indexing_delay_samples",
    } <= names
