"""
Market price reference and deal scoring for Vinted items.

Vinted does not expose any retail ("new") price for an item. To answer the
question "is this listing a good deal?", this module builds a reference price
from Vinted itself: for a freshly found item, it searches the catalog for
comparable listings (same brand, same significant keywords, same size) and
uses the median of their prices as the market reference.

Results are cached in the database so that a burst of similar items only
triggers a single extra catalog request.
"""

import re
import statistics
import time
from urllib.parse import quote_plus, urlparse

import db
from logger import get_logger
from pyVintedVN import Vinted

logger = get_logger(__name__)

# Words that carry no discriminating value when looking for comparable items.
STOPWORDS = {
    "a", "an", "the", "and", "or", "de", "des", "du", "la", "le", "les", "un",
    "une", "et", "pour", "avec", "sans", "en", "au", "aux", "sur", "par", "d",
    "l", "taille", "size", "neuf", "neuve", "new", "vintage", "occasion",
    "etat", "état", "tres", "très", "bon", "bonne", "comme", "jamais", "porte",
    "portee", "portée", "homme", "femme", "enfant", "unisexe", "original",
    "authentique", "authentic", "rare", "collector", "lot", "cm", "mm",
}

# A token must look like an actual word to be kept as a search keyword.
KEYWORD_RE = re.compile(r"[^\wàâäéèêëïîôöùûüÿçñ]+", re.UNICODE)

MAX_KEYWORDS = 4

# Vinted conditions grouped by how much they move a price. Comparing a
# brand-new item with a worn one is what makes a reference misleading, so
# comparables are restricted to the same group whenever there are enough.
CONDITION_GROUPS = {
    "new": {
        "neuf avec étiquette", "neuf sans étiquette", "new with tags",
        "new without tags", "nuovo con cartellino", "nuovo senza cartellino",
        "neu mit etikett", "neu ohne etikett", "nuevo con etiqueta",
        "nuevo sin etiqueta",
    },
    "good": {
        "très bon état", "very good", "ottime condizioni", "sehr gut",
        "muy bueno",
    },
    "worn": {
        "bon état", "satisfaisant", "good", "satisfactory", "buone condizioni",
        "discrete condizioni", "gut", "zufriedenstellend", "bueno",
        "satisfactorio",
    },
}


def condition_group(status):
    """
    Map a Vinted condition label to a coarse group.

    Args:
        status (str): The condition as returned by the API, any locale.

    Returns:
        str | None: "new", "good", "worn", or None when unrecognised.
    """
    normalised = (status or "").strip().lower()
    for group, labels in CONDITION_GROUPS.items():
        if normalised in labels:
            return group
    return None


def _to_float(value):
    """Convert a price-ish value to float, returning None when impossible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_int_parameter(key, default):
    """Read an integer parameter, falling back to a default when unusable."""
    value = db.get_parameter(key)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _get_float_parameter(key, default):
    """Read a float parameter, falling back to a default when unusable."""
    value = db.get_parameter(key)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def is_enabled():
    """Return True when the price reference feature is turned on."""
    return str(db.get_parameter("price_reference_enabled")).lower() == "true"


def extract_keywords(title, brand=None, size=None, max_keywords=MAX_KEYWORDS):
    """
    Reduce an item title to the few keywords that identify the product.

    Stopwords are dropped, the brand is not repeated, and the original word
    order is kept so that "nike air max" stays "nike air max". Numbers are
    kept, because model names rely on them ("air max 90", "levi's 501"), but
    the item size is filtered out since it says nothing about the product.

    Args:
        title (str): The item title.
        brand (str, optional): The item brand, excluded from the keywords.
        size (str, optional): The item size, excluded from the keywords.
        max_keywords (int, optional): Maximum number of keywords to keep.

    Returns:
        list[str]: The selected keywords, possibly empty.
    """
    brand_tokens = set()
    if brand:
        brand_tokens = {t for t in KEYWORD_RE.split(brand.lower()) if t}
    size_tokens = set()
    if size:
        size_tokens = {t for t in KEYWORD_RE.split(str(size).lower()) if t}

    keywords = []
    for token in KEYWORD_RE.split((title or "").lower()):
        if not token or token in STOPWORDS or token in brand_tokens:
            continue
        if token in size_tokens:
            continue
        # A long number is a model reference, a short one is a size.
        if token.isdigit() and not 2 <= len(token) <= 4:
            continue
        if not token.isdigit() and len(token) < 3:
            continue
        if token not in keywords:
            keywords.append(token)
        if len(keywords) >= max_keywords:
            break
    return keywords


def build_reference_query(locale, brand, keywords, size=None):
    """
    Build the Vinted catalog URL used to collect comparable listings.

    Args:
        locale (str): The Vinted domain to search on, e.g. "www.vinted.fr".
        brand (str): The item brand.
        keywords (list[str]): Significant keywords from the title.
        size (str, optional): The item size, added to narrow the comparison.

    Returns:
        str: A Vinted catalog search URL.
    """
    terms = []
    if brand:
        terms.append(brand)
    terms.extend(keywords)
    if size:
        terms.append(size)
    return f"https://{locale}/catalog?search_text={quote_plus(' '.join(terms))}"


def _filter_outliers(prices):
    """
    Drop listings whose price is not comparable to the rest of the sample.

    Vinted searches regularly return unrelated items: accessories in a search
    for shoes, or a ten-item bundle. Prices outside 1.5 interquartile ranges
    of the quartiles are discarded, which adapts to how spread out the sample
    actually is instead of applying a fixed ratio.

    Args:
        prices (list[float]): The raw prices.

    Returns:
        list[float]: The retained prices.
    """
    if len(prices) < 4:
        return prices
    ordered = sorted(prices)
    q1, q3 = (
        statistics.median(ordered[: len(ordered) // 2]),
        statistics.median(ordered[(len(ordered) + 1) // 2 :]),
    )
    spread = q3 - q1
    if spread <= 0:
        return prices
    low, high = q1 - 1.5 * spread, q3 + 1.5 * spread
    kept = [p for p in ordered if low <= p <= high]
    return kept if len(kept) >= 3 else prices


def _dispersion(prices, median):
    """
    Measure how spread out a sample is, as a percentage of its median.

    A tight sample means the reference describes a real market price; a wide
    one means the search returned a mix of different products.

    Args:
        prices (list[float]): The retained prices.
        median (float): The sample median.

    Returns:
        float: The standard deviation over the median, in percent.
    """
    if len(prices) < 2 or median <= 0:
        return 0.0
    return statistics.pstdev(prices) / median * 100


def get_market_reference(item, locale):
    """
    Compute the median price of listings comparable to the given item.

    Comparables are restricted to the item's condition group when enough of
    them share it, because condition moves prices more than anything else.
    The result is cached per (locale, brand, keywords, size, condition) for
    the number of hours configured in "price_reference_ttl_hours".

    Args:
        item (Item): The item to find a reference price for.
        locale (str): The Vinted domain to search on.

    Returns:
        dict | None: {"median", "currency", "sample_size", "dispersion",
            "condition_matched"} or None when no reliable reference could be
            computed.
    """
    size = item.size_title or ""
    keywords = extract_keywords(item.title, item.brand_title, size)
    if not keywords:
        # Without a single distinctive word, the search would compare the item
        # with the brand's whole catalogue rather than with the same product.
        logger.debug(f"No usable keywords for item {item.id}, skipping reference")
        return None

    group = condition_group(item.raw_data.get("status"))
    # Keywords are sorted in the cache key only, so that two wordings of the
    # same product ("ultra octaver uo300" and "uo300 ultra octave") share one
    # cache entry while each still searches with its own natural word order.
    cache_key = "|".join(
        [
            locale,
            (item.brand_title or "").lower(),
            "-".join(sorted(keywords)),
            size.lower(),
            group or "any",
        ]
    )

    ttl_hours = _get_float_parameter("price_reference_ttl_hours", 24)
    cached = db.get_price_reference(cache_key, ttl_hours * 3600)
    if cached is not None:
        return cached

    sample_size = _get_int_parameter("price_reference_sample_size", 20)
    min_samples = _get_int_parameter("price_reference_min_samples", 5)

    url = build_reference_query(locale, item.brand_title, keywords, size)
    try:
        comparables = Vinted().items.search(url, sample_size, 1)
    except Exception as e:
        logger.warning(f"Could not fetch price reference for item {item.id}: {e}")
        return None

    all_prices, same_condition = [], []
    for comparable in comparables:
        # The item we are pricing must not price itself.
        if str(comparable.id) == str(item.id):
            continue
        price = _to_float(comparable.price)
        if price is None or price <= 0:
            continue
        all_prices.append(price)
        if group and condition_group(comparable.raw_data.get("status")) == group:
            same_condition.append(price)

    # Same-condition comparables are better, but only when there are enough of
    # them: a tiny sample is worse than a slightly mismatched one.
    condition_matched = len(same_condition) >= min_samples
    prices = _filter_outliers(same_condition if condition_matched else all_prices)

    if len(prices) < min_samples:
        logger.debug(
            f"Only {len(prices)} comparables for item {item.id}, "
            f"need {min_samples}, skipping reference"
        )
        return None

    median = statistics.median(prices)
    reference = {
        "median": round(median, 2),
        "currency": item.currency,
        "sample_size": len(prices),
        "dispersion": round(_dispersion(prices, median), 1),
        "condition_matched": condition_matched,
    }
    db.set_price_reference(
        cache_key,
        reference["median"],
        reference["currency"],
        reference["sample_size"],
        reference["dispersion"],
        reference["condition_matched"],
    )
    return reference


def evaluate(item):
    """
    Compare an item price with its market reference and score the deal.

    This never raises: when anything goes wrong, or when the feature is
    disabled, placeholder values are returned so that the notification is
    still sent.

    Args:
        item (Item): The item to evaluate.

    Returns:
        dict: {"market_price", "discount", "deal", "sample_size",
            "discount_pct"} as display-ready values.
    """
    unknown = {
        "market_price": "n/a",
        "discount": "n/a",
        "deal": "❔ No reference",
        "sample_size": 0,
        # None means "unknown", which callers must not read as "bad deal".
        "discount_pct": None,
    }

    if not is_enabled():
        return unknown

    try:
        locale = urlparse(item.url).netloc or "www.vinted.fr"
        reference = get_market_reference(item, locale)
        if reference is None:
            return unknown

        price = _to_float(item.price)
        median = reference["median"]
        if price is None or median <= 0:
            return unknown

        # A sample spread this wide describes several different products, not
        # one market price, so no verdict is announced from it.
        dispersion = reference.get("dispersion") or 0
        max_dispersion = _get_float_parameter("price_reference_max_dispersion", 80)
        if max_dispersion and dispersion > max_dispersion:
            logger.debug(
                f"Reference for item {item.id} too scattered "
                f"({dispersion:.0f}%), no verdict"
            )
            return {
                **unknown,
                "market_price": f"{median:.2f} {reference['currency']}",
                "deal": f"❔ Unreliable reference (prices vary by {dispersion:.0f}%)",
                "sample_size": reference["sample_size"],
            }

        # Positive means the item is cheaper than the market reference.
        discount = (median - price) / median * 100
        hot = _get_float_parameter("deal_threshold_hot", 50)
        good = _get_float_parameter("deal_threshold_good", 25)

        if discount >= hot:
            deal = "🔥 EXCELLENT DEAL"
        elif discount >= good:
            deal = "✅ Good deal"
        elif discount >= 0:
            deal = "➖ Fair price"
        else:
            deal = "⚠️ Above market price"

        basis = "same condition" if reference.get("condition_matched") else "all conditions"
        return {
            "market_price": f"{median:.2f} {reference['currency']}",
            # round() first so that a negligible gap never renders as "-0%".
            "discount": f"{round(-discount):+d}% vs market",
            "deal": f"{deal} ({reference['sample_size']} listings, {basis})",
            "sample_size": reference["sample_size"],
            "discount_pct": discount,
        }
    except Exception as e:
        logger.warning(f"Price evaluation failed for item {item.id}: {e}")
        return unknown


def should_notify(evaluation):
    """
    Decide whether an item deserves a notification at all.

    Items with no market reference are always notified: not knowing a price
    is not a reason to hide a listing.

    Args:
        evaluation (dict): The result of evaluate().

    Returns:
        bool: True when the item must be sent.
    """
    discount = evaluation.get("discount_pct")
    if discount is None:
        return True
    threshold = db.get_parameter("notify_skip_below")
    if threshold in (None, ""):
        return True
    try:
        return discount >= float(threshold)
    except (TypeError, ValueError):
        return True


def is_silent(evaluation):
    """
    Decide whether a notification should arrive without a sound.

    Items with no market reference stay audible, so that disabling the
    reference engine restores the original behaviour.

    Args:
        evaluation (dict): The result of evaluate().

    Returns:
        bool: True when the notification must be silent.
    """
    discount = evaluation.get("discount_pct")
    if discount is None:
        return False
    threshold = db.get_parameter("notify_silent_below")
    if threshold in (None, ""):
        return False
    try:
        return discount < float(threshold)
    except (TypeError, ValueError):
        return False
