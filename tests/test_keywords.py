"""Turning a listing title into search keywords."""

import price_reference as pr


def test_keeps_model_numbers_and_drops_the_size():
    # "90" identifies the model, "42" is only the size: keeping the size would
    # compare an Air Max 90 with every shoe of that size.
    assert pr.extract_keywords("Nike Air Max 90 taille 42", "Nike", "42") == [
        "air",
        "max",
        "90",
    ]


def test_drops_stopwords_across_languages():
    cases = [
        ("Vestido Zara nuevo talla M muy bueno", "Zara", "M", ["vestido"]),
        ("Nike Sneaker neu ohne etikett", "Nike", "42", ["sneaker"]),
        ("Zara jurkjes nieuw maat 38", "Zara", "38", ["jurkjes"]),
        ("Microfono nuovo con cartellino", "Behringer", "", ["microfono"]),
        ("Jean très bon état", "Levi's", "42", ["jean"]),
    ]
    for title, brand, size, expected in cases:
        assert pr.extract_keywords(title, brand, size) == expected, title


def test_brand_words_are_not_repeated_as_keywords():
    assert "nike" not in pr.extract_keywords("Nike sweatshirt", "Nike", "M")


def test_title_with_nothing_distinctive_yields_no_keyword():
    # Such an item must not be priced against the brand's whole catalogue.
    assert pr.extract_keywords("Nike air", "Nike Air", "") == []


def test_caps_the_number_of_keywords():
    keywords = pr.extract_keywords(
        "veste bomber matelassee reversible capuche amovible", "Zara", "M"
    )
    assert len(keywords) <= pr.MAX_KEYWORDS


def test_a_split_model_reference_survives():
    # "TD-3" becomes a two-letter word and a single digit, both under a length
    # threshold. Dropping them left "decksaver", which priced a synthesiser
    # against plastic covers.
    keywords = pr.extract_keywords("TD-3 AM Behringer + Decksaver", "Behringer", "")
    assert "td" in keywords and "3" in keywords


def test_a_lone_digit_after_a_word_is_part_of_the_model():
    assert "1" in pr.extract_keywords("Softube Console 1 Mk III", "Softube", "")


def test_a_stray_digit_on_its_own_is_still_ignored():
    # Nothing precedes it, so it identifies no model.
    assert "2" not in pr.extract_keywords("2 pulls", "Zara", "")


def test_a_size_in_the_title_is_never_taken_for_a_model():
    assert "1" not in pr.extract_keywords("Robe portefeuille 1", "Zara", "1")


def test_a_model_number_outranks_generic_words():
    # The budget is four words and the model sits last in the title.
    keywords = pr.extract_keywords(
        "Equalizzatore grafico Behringer ultra curve DSP 8000", "Behringer", ""
    )
    assert "dsp" in keywords and "8000" in keywords


def test_word_order_follows_the_title_after_ranking():
    keywords = pr.extract_keywords(
        "Equalizzatore grafico Behringer ultra curve DSP 8000", "Behringer", ""
    )
    assert keywords == sorted(
        keywords,
        key=lambda word: "equalizzatore grafico ultra curve dsp 8000".index(word),
    )
