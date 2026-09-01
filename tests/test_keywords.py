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
