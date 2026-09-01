"""Deciding what to send, and rendering it."""

import core
import price_reference as pr


def evaluation(discount):
    return {"discount_pct": discount, "discount": "x", "deal": "y"}


def test_a_deal_is_announced_out_loud(database):
    database.set_parameter("notify_silent_below", "25")
    assert pr.is_silent(evaluation(60)) is False
    assert pr.should_notify(evaluation(60)) is True


def test_a_mediocre_price_arrives_silently(database):
    database.set_parameter("notify_silent_below", "25")
    assert pr.is_silent(evaluation(10)) is True


def test_an_unknown_price_never_hides_a_listing(database):
    # Not knowing a price is not a reason to silence or drop an item.
    database.set_parameter("notify_silent_below", "25")
    database.set_parameter("notify_skip_below", "0")
    assert pr.is_silent(evaluation(None)) is False
    assert pr.should_notify(evaluation(None)) is True


def test_skip_threshold_drops_overpriced_items(database):
    database.set_parameter("notify_skip_below", "0")
    assert pr.should_notify(evaluation(-20)) is False
    assert pr.should_notify(evaluation(5)) is True


def test_no_skip_threshold_means_everything_is_sent(database):
    database.set_parameter("notify_skip_below", "")
    assert pr.should_notify(evaluation(-80)) is True


def test_message_escapes_text_coming_from_vinted(database, item):
    database.set_parameter("message_template", "{title} / {brand}")
    database.set_parameter("price_reference_enabled", "False")
    rendered = core.build_item_message(item(title="Veste <b>x</b>", brand="A & B"))
    assert "&lt;b&gt;" in rendered and "&amp;" in rendered
    assert "<b>" not in rendered


def test_unknown_placeholder_does_not_break_the_message(database, item):
    database.set_parameter("message_template", "{title} {nonexistent}")
    database.set_parameter("price_reference_enabled", "False")
    assert "Nike Air Max 90" in core.build_item_message(item())


def test_message_exposes_the_fields_the_api_already_returned(database, item):
    database.set_parameter(
        "message_template", "{price}|{total_price}|{status}|{size}|{favourites}|{views}"
    )
    database.set_parameter("price_reference_enabled", "False")
    rendered = core.build_item_message(item())
    assert rendered == "30.0 EUR|32.20 EUR|Très bon état|42|3|7"


def test_disabled_engine_reports_no_reference(database, item):
    database.set_parameter("price_reference_enabled", "False")
    result = pr.evaluate(item())
    assert result["discount_pct"] is None
    assert result["market_price"] == "n/a"
