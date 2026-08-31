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

    Vinted searches regularly return a few unrelated items (a single sock in a
    search for a jacket, or a bundle of ten). Anything below a fifth or above
    five times the raw median is considered noise.

    Args:
        prices (list[float]): The raw prices.

    Returns:
        list[float]: The retained prices.
    """
    if len(prices) < 3:
        return prices
    raw_median = statistics.median(prices)
    if raw_median <= 0:
        return prices
    return [p for p in prices if raw_median / 5 <= p <= raw_median * 5]


def get_market_reference(item, locale):
    """
    Compute the median price of listings comparable to the given item.

    The result is cached per (locale, brand, keywords, size) for the number of
    hours configured in the "price_reference_ttl_hours" parameter.

    Args:
        item (Item): The item to find a reference price for.
        locale (str): The Vinted domain to search on.

    Returns:
        dict | None: {"median", "currency", "sample_size"} or None when no
            reliable reference could be computed.
    """
    size = item.size_title or ""
    keywords = extract_keywords(item.title, item.brand_title, size)
    if not keywords and not item.brand_title:
        logger.debug(f"No usable keywords for item {item.id}, skipping reference")
        return None

    cache_key = f"{locale}|{(item.brand_title or '').lower()}|{'-'.join(keywords)}|{size.lower()}"

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

    prices = []
    for comparable in comparables:
        # The item we are pricing must not price itself.
        if str(comparable.id) == str(item.id):
            continue
        price = _to_float(comparable.price)
        if price is not None and price > 0:
            prices.append(price)

    prices = _filter_outliers(prices)
    if len(prices) < min_samples:
        logger.debug(
            f"Only {len(prices)} comparables for item {item.id}, "
            f"need {min_samples}, skipping reference"
        )
        return None

    reference = {
        "median": round(statistics.median(prices), 2),
        "currency": item.currency,
        "sample_size": len(prices),
    }
    db.set_price_reference(
        cache_key, reference["median"], reference["currency"], reference["sample_size"]
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
        dict: {"market_price", "discount", "deal", "sample_size"} as
            display-ready strings.
    """
    unknown = {
        "market_price": "n/a",
        "discount": "n/a",
        "deal": "❔ No reference",
        "sample_size": 0,
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

        return {
            "market_price": f"{median:.2f} {reference['currency']}",
            # round() first so that a negligible gap never renders as "-0%".
            "discount": f"{round(-discount):+d}% vs market",
            "deal": f"{deal} (based on {reference['sample_size']} listings)",
            "sample_size": reference["sample_size"],
        }
    except Exception as e:
        logger.warning(f"Price evaluation failed for item {item.id}: {e}")
        return unknown
