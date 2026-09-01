"""Building a market reference out of comparable listings."""

import price_reference as pr


def test_interquartile_filter_drops_unrelated_prices():
    prices = [18, 20, 21, 22, 23, 25, 900]
    assert 900 not in pr._filter_outliers(prices)


def test_filter_keeps_a_tight_sample_intact():
    prices = [20, 21, 22, 23, 24]
    assert pr._filter_outliers(prices) == sorted(prices)


def test_filter_gives_up_rather_than_emptying_the_sample():
    # Cutting this sample down would leave too little to compute anything, so
    # the original is returned instead of an unusable remainder.
    prices = [1, 2, 100, 200]
    assert len(pr._filter_outliers(prices)) >= 3


def test_dispersion_reflects_how_spread_out_a_sample_is():
    assert pr._dispersion([20, 20, 20, 20], 20) == 0
    assert pr._dispersion([5, 20, 60], 20) > 50


def test_condition_groups_recognise_every_locale():
    assert pr.condition_group("Neuf avec étiquette") == "new"
    assert pr.condition_group("New with tags") == "new"
    assert pr.condition_group("Nuovo con cartellino") == "new"
    assert pr.condition_group("Très bon état") == "good"
    assert pr.condition_group("Bon état") == "worn"
    assert pr.condition_group("something unknown") is None


def test_catalog_filter_is_read_from_the_monitored_query():
    url = "https://www.vinted.fr/catalog?search_text=nike&catalog[]=1242&catalog[]=16"
    assert pr.extract_catalog_ids(url) == ["1242", "16"]
    assert (
        pr.extract_catalog_ids("https://www.vinted.fr/catalog?search_text=nike") == []
    )
    assert pr.extract_catalog_ids(None) == []


def test_encoded_catalog_filter_is_read_too():
    # The web UI stores the query with the brackets percent-encoded.
    url = "https://www.vinted.fr/catalog?search_text=behringer&catalog%5B%5D=2994"
    assert pr.extract_catalog_ids(url) == ["2994"]


def test_reference_query_carries_brand_keywords_size_and_category():
    url = pr.build_reference_query(
        "www.vinted.fr", "Nike", ["air", "max"], "42", ["1242"]
    )
    assert url.startswith("https://www.vinted.fr/catalog?search_text=")
    assert "Nike+air+max+42" in url
    assert "catalog[]=1242" in url
