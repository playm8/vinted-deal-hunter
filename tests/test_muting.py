"""Muting a brand or a seller from a notification."""

import core


class FakeItemWithSeller:
    def __init__(self, brand="Nike", seller="42", name="bob"):
        self.brand_title = brand
        self.raw_data = {"user": {"id": seller, "login": name}}


def test_seller_is_read_from_the_payload():
    assert core.seller_id(FakeItemWithSeller()) == "42"
    assert core.seller_name(FakeItemWithSeller()) == "bob"


def test_a_missing_seller_is_not_an_error():
    class NoUser:
        brand_title = "Nike"
        raw_data = {}

    assert core.seller_id(NoUser()) is None
    assert core.seller_name(NoUser()) is None


def test_muted_brand_is_recognised_whatever_the_case():
    item = FakeItemWithSeller(brand="Nike")
    assert core.is_muted(item, {"nike"}, set()) is True
    assert core.is_muted(item, {"adidas"}, set()) is False


def test_muted_seller_is_recognised():
    item = FakeItemWithSeller(seller="42")
    assert core.is_muted(item, set(), {"42"}) is True
    assert core.is_muted(item, set(), {"99"}) is False


def test_nothing_muted_lets_everything_through():
    assert core.is_muted(FakeItemWithSeller(), set(), set()) is False


def test_brands_round_trip_through_the_database(database):
    assert database.ignore_brand("Nike") is True
    # Muting twice must not raise, it is a button anyone can press again.
    assert database.ignore_brand("Nike") is False
    assert "Nike" in database.get_ignored_brands()
    assert database.unignore_brand("Nike") is True
    assert database.unignore_brand("Nike") is False
    assert database.get_ignored_brands() == []


def test_sellers_round_trip_through_the_database(database):
    assert database.ignore_seller("42", "bob") is True
    assert database.ignore_seller("42", "bob") is False
    assert "42" in database.get_ignored_sellers()
    assert database.unignore_seller("42") is True


def test_the_log_records_what_an_action_needs(database):
    database.add_notification_log(
        1,
        "Nike Air",
        30,
        "EUR",
        "https://x",
        20,
        "deal",
        False,
        False,
        brand="Nike",
        seller_id="42",
        seller_name="bob",
    )
    logged = database.get_logged_item(1)
    assert logged["brand"] == "Nike"
    assert logged["seller_id"] == "42"
    assert logged["seller_name"] == "bob"


def test_an_unknown_item_yields_nothing(database):
    assert database.get_logged_item(999) is None
