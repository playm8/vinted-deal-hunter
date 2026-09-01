"""Keeping credentials out of the database and out of the browser."""

import db
import pytest


def test_environment_wins_over_the_database(database, monkeypatch):
    database.set_parameter("telegram_token", "from-db")
    monkeypatch.setenv("TELEGRAM_TOKEN", "from-env")
    assert database.get_secret("telegram_token") == "from-env"
    assert database.secret_is_from_env("telegram_token") is True


def test_database_is_used_when_the_environment_is_silent(database, monkeypatch):
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    database.set_parameter("telegram_token", "from-db")
    assert database.get_secret("telegram_token") == "from-db"
    assert database.secret_is_from_env("telegram_token") is False


def test_an_empty_variable_does_not_hide_the_database(database, monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "")
    database.set_parameter("telegram_token", "from-db")
    assert database.get_secret("telegram_token") == "from-db"


def test_ordinary_settings_are_not_treated_as_secrets(database):
    assert db.secret_is_from_env("query_refresh_delay") is False


@pytest.fixture
def client(database, monkeypatch):
    monkeypatch.delenv("WEB_UI_PASSWORD", raising=False)
    import importlib

    import web_ui_plugin.web_ui as web_ui

    importlib.reload(web_ui)
    web_ui.app.config["TESTING"] = True
    return web_ui.app.test_client()


def test_the_page_never_shows_the_token(client, database):
    database.set_parameter("telegram_token", "123456:SECRETVALUE")
    body = client.get("/config").get_data(as_text=True)
    assert "SECRETVALUE" not in body
    assert 'type="password"' in body


def test_an_empty_field_keeps_the_stored_value(client, database):
    database.set_parameter("telegram_token", "keep-me")
    client.post("/update_config", data={"telegram_token": ""})
    assert database.get_parameter("telegram_token") == "keep-me"


def test_a_dash_clears_the_value(client, database):
    database.set_parameter("telegram_token", "clear-me")
    client.post("/update_config", data={"telegram_token": "-"})
    assert database.get_parameter("telegram_token") == ""


def test_a_new_value_replaces_the_old_one(client, database):
    database.set_parameter("telegram_token", "old")
    client.post("/update_config", data={"telegram_token": "new"})
    assert database.get_parameter("telegram_token") == "new"


def test_environment_managed_secrets_are_not_overwritten(client, database, monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "from-env")
    database.set_parameter("telegram_token", "")
    client.post("/update_config", data={"telegram_token": "typed-anyway"})
    assert database.get_parameter("telegram_token") == ""


def test_without_a_password_the_interface_stays_open(client):
    assert client.get("/config").status_code == 200


def test_a_password_makes_the_interface_ask_for_one(database, monkeypatch):
    monkeypatch.setenv("WEB_UI_PASSWORD", "s3cret")
    import importlib

    import web_ui_plugin.web_ui as web_ui

    importlib.reload(web_ui)
    client = web_ui.app.test_client()
    assert client.get("/config").status_code == 401

    import base64

    token = base64.b64encode(b"admin:s3cret").decode()
    ok = client.get("/config", headers={"Authorization": f"Basic {token}"})
    assert ok.status_code == 200

    wrong = base64.b64encode(b"admin:nope").decode()
    assert (
        client.get("/config", headers={"Authorization": f"Basic {wrong}"}).status_code
        == 401
    )


def test_the_warning_shows_by_default(client):
    assert "not password protected" in client.get("/config").get_data(as_text=True)


def test_the_warning_can_be_acknowledged(client, database):
    # Access may already be restricted by a VPN or a private network, and a
    # warning that cannot be silenced is one people stop reading.
    database.set_parameter("web_ui_auth_warning", "False")
    assert "not password protected" not in client.get("/config").get_data(as_text=True)


def test_the_warning_never_shows_when_a_password_is_set(database, monkeypatch):
    monkeypatch.setenv("WEB_UI_PASSWORD", "s3cret")
    import base64
    import importlib

    import web_ui_plugin.web_ui as web_ui

    importlib.reload(web_ui)
    token = base64.b64encode(b"admin:s3cret").decode()
    body = (
        web_ui.app.test_client()
        .get("/config", headers={"Authorization": f"Basic {token}"})
        .get_data(as_text=True)
    )
    assert "not password protected" not in body
