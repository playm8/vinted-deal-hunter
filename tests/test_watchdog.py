"""Noticing that the pipeline has gone quiet."""

import core


def test_stays_silent_below_the_threshold(database):
    database.set_parameter("watchdog_cycles", "30")
    for _ in range(29):
        core.record_scrape_outcome(found=20, kept=0)
    assert core.pending_watchdog_alert() is None


def test_alerts_once_the_threshold_is_reached(database):
    database.set_parameter("watchdog_cycles", "30")
    for _ in range(30):
        core.record_scrape_outcome(found=20, kept=0)
    alert = core.pending_watchdog_alert()
    assert alert is not None
    # The message must say what to do, not only that something is wrong.
    assert "Maximum Item Age" in alert


def test_does_not_repeat_itself(database):
    database.set_parameter("watchdog_cycles", "5")
    for _ in range(5):
        core.record_scrape_outcome(found=20, kept=0)
    assert core.pending_watchdog_alert() is not None
    assert core.pending_watchdog_alert() is None


def test_a_genuinely_quiet_period_is_not_a_failure(database):
    # Searches returning nothing means there is nothing to sell, not a bug.
    database.set_parameter("watchdog_cycles", "5")
    for _ in range(50):
        core.record_scrape_outcome(found=0, kept=0)
    assert core.pending_watchdog_alert() is None


def test_recovery_rearms_the_alarm(database):
    database.set_parameter("watchdog_cycles", "5")
    for _ in range(5):
        core.record_scrape_outcome(found=20, kept=0)
    core.pending_watchdog_alert()
    core.record_scrape_outcome(found=20, kept=2)
    assert database.get_parameter("watchdog_empty_cycles") == "0"
    for _ in range(5):
        core.record_scrape_outcome(found=20, kept=0)
    assert core.pending_watchdog_alert() is not None


def test_can_be_turned_off(database):
    database.set_parameter("watchdog_enabled", "False")
    database.set_parameter("watchdog_cycles", "1")
    core.record_scrape_outcome(found=20, kept=0)
    assert core.pending_watchdog_alert() is None
