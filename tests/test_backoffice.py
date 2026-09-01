"""Pages that expose what the database already recorded."""

import pytest


@pytest.fixture
def client(database, monkeypatch):
    monkeypatch.delenv("WEB_UI_PASSWORD", raising=False)
    import importlib

    import web_ui_plugin.web_ui as web_ui

    importlib.reload(web_ui)
    web_ui.app.config["TESTING"] = True
    return web_ui.app.test_client()


def test_muted_page_lists_nothing_when_nothing_is_muted(client):
    body = client.get("/muted").get_data(as_text=True)
    assert "No muted brands" in body


def test_muted_page_lists_what_was_muted(client, database):
    database.ignore_brand("Nike")
    database.ignore_seller("42", "bob")
    body = client.get("/muted").get_data(as_text=True)
    assert "Nike" in body and "bob" in body


def test_unmuting_from_the_page_works(client, database):
    database.ignore_brand("Nike")
    client.post("/unmute/brand/Nike", follow_redirects=True)
    assert database.get_ignored_brands() == []


def test_unmuting_a_seller_works(client, database):
    # Only reachable from the web: there is no Telegram command for it.
    database.ignore_seller("42", "bob")
    client.post("/unmute/seller/42", follow_redirects=True)
    assert database.get_ignored_sellers() == []


def test_unmuting_something_absent_says_so(client):
    body = client.post("/unmute/brand/Ghost", follow_redirects=True).get_data(
        as_text=True
    )
    assert "Was not muted" in body or "pas en sourdine" in body


def test_brand_names_from_vinted_are_escaped(client, database):
    # First place third-party data reaches the backoffice.
    database.ignore_brand("<script>alert(1)</script>")
    body = client.get("/muted").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body


def test_unmuting_only_accepts_post(client):
    assert client.get("/unmute/brand/Nike").status_code == 405


def test_notifications_page_shows_the_decisions(client, database):
    database.add_notification_log(
        1,
        "Nike Air",
        30,
        "EUR",
        "https://x",
        62.0,
        "EXCELLENT",
        False,
        False,
        brand="Nike",
        seller_id="42",
        seller_name="bob",
    )
    database.add_notification_log(
        2,
        "Overpriced",
        99,
        "EUR",
        "https://y",
        -40.0,
        "Above",
        False,
        True,
        brand="Zara",
    )
    body = client.get("/notifications").get_data(as_text=True)
    assert "Nike Air" in body and "Overpriced" in body
    # The skipped one is explained rather than simply absent.
    assert "Skipped" in body or "Ignorés" in body


def test_notifications_page_is_fine_when_empty(client):
    assert client.get("/notifications").status_code == 200


def test_backup_button_writes_a_backup(client, database, tmp_path):
    database.set_parameter("backup_directory", str(tmp_path / "bk"))
    client.post("/backup", follow_redirects=True)
    import os

    assert os.listdir(str(tmp_path / "bk"))
