"""Shared translations and the trend lines."""

import core
import translations
from web_ui_plugin.sparkline import sparkline


def test_pipeline_messages_follow_the_selected_language(database):
    database.set_parameter("ui_language", "fr")
    message, _ = core.process_query("not-a-vinted-url")
    assert message  # whatever it says, it must not crash
    database.set_parameter("ui_language", "en")
    assert translations.translate("Query added.") == "Query added."
    database.set_parameter("ui_language", "fr")
    assert translations.translate("Query added.") == "Recherche ajoutée."


def test_an_untranslated_message_falls_back_to_english(database):
    database.set_parameter("ui_language", "fr")
    assert translations.translate("Something never translated") == (
        "Something never translated"
    )


def test_summary_placeholders_survive_translation(database):
    database.set_parameter("ui_language", "fr")
    rendered = translations.translate("Items found: {count}").format(count=7)
    assert "7" in rendered


def test_a_line_needs_at_least_two_points():
    assert sparkline([("2026-01-01", 10)]) is None
    assert sparkline([]) is None
    assert sparkline([("2026-01-01", 10), ("2026-01-02", 12)]) is not None


def test_a_flat_series_does_not_divide_by_zero():
    line = sparkline([("a", 5), ("b", 5), ("c", 5)])
    assert line["direction"] == "flat"
    assert "nan" not in line["points"]


def test_direction_reflects_first_and_last_values():
    assert sparkline([("a", 10), ("b", 20)])["direction"] == "up"
    assert sparkline([("a", 20), ("b", 10)])["direction"] == "down"


def test_points_stay_inside_the_drawing_area():
    line = sparkline([("a", 1), ("b", 100), ("c", 50)], width=160, height=36)
    for pair in line["points"].split():
        x, y = (float(value) for value in pair.split(","))
        assert 0 <= x <= 160
        assert 0 <= y <= 36


def test_series_needs_two_distinct_days(database):
    from time import time

    now = time()
    for day_offset, price in ((0, 20), (0, 22)):
        database.add_price_reference_history("Nike", "air max", price, "EUR", 10, 20.0)
    # Both samples land on the same day, so there is no trend to draw yet.
    assert database.get_price_history_series() == []
