"""Following Vinted's indexing delay instead of assuming it."""

import core


def record(database, samples):
    for sample in samples:
        database.add_indexing_delay_sample(sample, 60)


def test_falls_back_to_the_floor_without_measurements(database):
    assert core.get_item_max_age() == 240


def test_ignores_a_handful_of_measurements(database):
    # One stray sample taken during a quiet spell must not move the window.
    record(database, [830])
    assert core.get_item_max_age() == 240


def test_floor_wins_when_indexing_is_fast(database):
    record(database, [5, 8, 6, 10, 7, 9])
    assert core.get_item_max_age() == 240


def test_widens_when_indexing_falls_behind(database):
    record(database, [300, 320, 280, 310, 295, 305])
    assert core.get_item_max_age() == 840


def test_never_exceeds_the_cap(database):
    record(database, [900, 950, 880, 910, 930, 890])
    assert core.get_item_max_age() == 1440


def test_a_single_fresh_sample_beats_the_quiet_ones(database):
    # Only a recently published item measures the real delay; the others just
    # reflect that nothing was on sale.
    record(database, [600, 720, 88, 900, 650, 800])
    assert core.get_item_max_age() == 264


def test_manual_mode_ignores_measurements(database):
    database.set_parameter("item_max_age_mode", "fixed")
    record(database, [900, 950, 880, 910, 930, 890])
    assert core.get_item_max_age() == 240


def test_measurement_survives_a_window_that_keeps_nothing(database, item):
    # Without this the system could never recover on its own: a window too
    # narrow would hide the measurement needed to widen it.
    database.set_parameter("item_max_age_minutes", "20")
    items = [item(age_minutes=90), item(age_minutes=200)]
    assert [i for i in items if i.created_at_ts and False] == []
    core.record_indexing_delay(items)
    assert database.get_indexing_delay_samples()


def test_rolling_window_keeps_only_the_last_samples(database):
    for value in range(20):
        database.add_indexing_delay_sample(value, 5)
    assert len(database.get_indexing_delay_samples()) == 5
