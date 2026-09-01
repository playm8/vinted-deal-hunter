"""Recognising a price drop without becoming noisy."""

import core
import price_drop


def row(baseline=100, first=100, notified=None):
    return {
        "drop_baseline_price": baseline,
        "first_price": first,
        "last_price": baseline,
        "drop_notified_at": notified,
    }


def test_a_real_drop_is_announced(database):
    drop = price_drop.evaluate_drop(row(baseline=100), 80, now=1000)
    assert drop["drop_pct"] == 20
    assert drop["drop_amount"] == 20


def test_a_small_percentage_is_ignored(database):
    assert price_drop.evaluate_drop(row(baseline=100), 95, now=1000) is None


def test_a_big_percentage_on_a_small_price_is_ignored(database):
    # 8 to 7 is 12.5%, over the relative threshold. The absolute one is what
    # keeps cheap items from being noisy.
    assert price_drop.evaluate_drop(row(baseline=8), 7, now=1000) is None


def test_both_thresholds_must_be_met(database):
    database.set_parameter("price_drop_min_pct", "10")
    database.set_parameter("price_drop_min_amount", "3")
    assert price_drop.evaluate_drop(row(baseline=100), 89, now=1000) is not None
    assert price_drop.evaluate_drop(row(baseline=20), 18, now=1000) is None


def test_a_price_going_up_is_not_a_drop(database):
    assert price_drop.evaluate_drop(row(baseline=100), 120, now=1000) is None


def test_an_unchanged_price_is_not_a_drop(database):
    assert price_drop.evaluate_drop(row(baseline=100), 100, now=1000) is None


def test_the_cooldown_holds(database):
    database.set_parameter("price_drop_cooldown_hours", "24")
    recent = row(baseline=100, notified=1000)
    assert price_drop.evaluate_drop(recent, 80, now=1000 + 3600) is None
    assert price_drop.evaluate_drop(recent, 80, now=1000 + 25 * 3600) is not None


def test_an_oscillating_price_alerts_once(database):
    # The failure this design exists to prevent: a seller moving a price up
    # and down must not alert on every cycle. The baseline only follows a
    # drop downwards, so the recovery is never a new reference.
    current = row(baseline=100)
    first = price_drop.evaluate_drop(current, 70, now=1000)
    assert first is not None

    # A drop was announced: the baseline moves down to the new price.
    current["drop_baseline_price"] = 70
    current["drop_notified_at"] = 1000

    # Price goes back up, then down to 70 again, well after the cooldown.
    assert price_drop.evaluate_drop(current, 100, now=1000 + 40 * 3600) is None
    assert price_drop.evaluate_drop(current, 70, now=1000 + 41 * 3600) is None


def test_it_can_be_turned_off(database):
    database.set_parameter("price_drop_enabled", "False")
    assert price_drop.evaluate_drop(row(baseline=100), 10, now=1000) is None


def test_a_row_without_a_baseline_falls_back_to_the_first_price(database):
    without = {"drop_baseline_price": None, "first_price": 100}
    assert price_drop.evaluate_drop(without, 70, now=1000) is not None


def test_a_row_with_no_price_at_all_is_skipped(database):
    assert price_drop.evaluate_drop({}, 70, now=1000) is None


def test_prices_arriving_as_strings_are_read(database):
    # The API returns strings, the column is NUMERIC: both forms turn up.
    assert price_drop.to_price("30.0") == 30.0
    assert price_drop.to_price(30) == 30.0
    assert price_drop.to_price(None) is None
    assert price_drop.to_price("free") is None


def test_the_message_leads_with_the_drop(database, item):
    database.set_parameter("message_template", "{title}")
    database.set_parameter("price_reference_enabled", "False")
    drop = {"baseline": 100, "new_price": 70, "drop_pct": 30, "drop_amount": 30}
    rendered = core.build_item_message(item(), drop=drop)
    assert rendered.startswith("📉")
    assert "100" in rendered and "70" in rendered
    # The item message is still there, under the header.
    assert "Nike Air Max 90" in rendered


def queued(new_items_queue):
    """Drain a queue into a list of messages."""
    import time

    time.sleep(0.3)  # multiprocessing.Queue.put is asynchronous
    out = []
    while not new_items_queue.empty():
        out.append(new_items_queue.get())
    return out


def run_cycle(database, items, query_id=1):
    """Push items through clear_item_queue and return what came out."""
    import time
    from multiprocessing import Queue

    items_queue, new_items_queue = Queue(), Queue()
    items_queue.put((items, query_id))
    time.sleep(0.3)
    core.clear_item_queue(items_queue, new_items_queue)
    return queued(new_items_queue)


def test_a_known_item_that_dropped_is_notified_again(database, item):
    database.set_parameter("price_reference_enabled", "False")
    database.set_parameter("daily_summary_enabled", "False")
    database.set_parameter("watchdog_enabled", "False")
    database.add_query_to_db("https://www.vinted.fr/catalog?search_text=x", "q")

    first = item(id=77, price="100.0")
    assert run_cycle(database, [first])  # first sighting notifies

    cheaper = item(id=77, price="70.0")
    messages = run_cycle(database, [cheaper])
    assert len(messages) == 1
    assert messages[0][0].startswith("📉")


def test_a_known_item_at_the_same_price_stays_quiet(database, item):
    database.set_parameter("price_reference_enabled", "False")
    database.set_parameter("daily_summary_enabled", "False")
    database.set_parameter("watchdog_enabled", "False")
    database.add_query_to_db("https://www.vinted.fr/catalog?search_text=x", "q")

    same = item(id=88, price="100.0")
    assert run_cycle(database, [same])
    assert run_cycle(database, [same]) == []


def test_a_muted_brand_cannot_return_through_a_drop(database, item):
    # The most visible way to break trust in the mute button.
    database.set_parameter("price_reference_enabled", "False")
    database.set_parameter("daily_summary_enabled", "False")
    database.set_parameter("watchdog_enabled", "False")
    database.add_query_to_db("https://www.vinted.fr/catalog?search_text=x", "q")

    expensive = item(id=99, price="100.0", brand="Nike")
    run_cycle(database, [expensive])
    database.ignore_brand("Nike")

    cheaper = item(id=99, price="50.0", brand="Nike")
    assert run_cycle(database, [cheaper]) == []


def test_an_old_unknown_item_is_not_announced(database, item):
    # Passing every item on must not turn a newly added query into a flood.
    database.set_parameter("price_reference_enabled", "False")
    database.set_parameter("daily_summary_enabled", "False")
    database.set_parameter("watchdog_enabled", "False")
    database.add_query_to_db("https://www.vinted.fr/catalog?search_text=x", "q")

    ancient = item(id=123, age_minutes=60 * 24 * 30)
    assert run_cycle(database, [ancient]) == []


def test_no_more_drops_than_the_cycle_allows(database, item):
    database.set_parameter("price_reference_enabled", "False")
    database.set_parameter("daily_summary_enabled", "False")
    database.set_parameter("watchdog_enabled", "False")
    database.set_parameter("price_drop_max_per_cycle", "2")
    database.add_query_to_db("https://www.vinted.fr/catalog?search_text=x", "q")

    originals = [item(id=200 + n, price="100.0") for n in range(5)]
    run_cycle(database, originals)
    cheaper = [item(id=200 + n, price="50.0") for n in range(5)]
    assert len(run_cycle(database, cheaper)) == 2
