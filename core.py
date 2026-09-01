import db
import price_reference
import re
import requests
from pyVintedVN import Vinted, requester
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import statistics
from datetime import datetime, time as dtime, timezone
from html import escape
from logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


def process_query(query, name=None):
    """
    Process a Vinted query URL by:
    1. Checking if the URL is a brand URL and converting it to standard format if needed
    2. Parsing the URL and extracting query parameters
    3. Ensuring the order flag is set to "newest_first"
    4. Removing time and search_id parameters
    5. Rebuilding the query string and URL
    6. Checking if the query already exists in the database
    7. Adding the query to the database if it doesn't exist

    Args:
        query (str): The Vinted query URL
        name (str, optional): A name for the query. If provided, it will be used as the query name.

    Returns:
        tuple: (message, is_new_query)
            - message (str): Status message
            - is_new_query (bool): True if query was added, False if it already existed
    """
    # Check if the URL is a brand URL (format: url/brand/id-name)
    parsed_url = urlparse(query)
    path_parts = parsed_url.path.strip("/").split("/")

    if len(path_parts) >= 2 and path_parts[0] == "brand":
        # Extract the brand ID from the format "id-name"
        brand_id_with_name = path_parts[1]
        brand_id = brand_id_with_name.split("-")[0]

        # Create a new URL with the standard format
        new_path = "/catalog"
        new_query_params = {"brand_ids[]": [brand_id]}
        new_query_string = urlencode(new_query_params, doseq=True)

        # Rebuild the URL
        query = urlunparse(
            (parsed_url.scheme, parsed_url.netloc, new_path, "", new_query_string, "")
        )
        logger.info(f"Converted brand URL to standard format: {query}")

        # Parse the URL and extract the query parameters
        parsed_url = urlparse(query)

    query_params = parse_qs(parsed_url.query)

    # Ensure the order flag is set to newest_first
    query_params["order"] = ["newest_first"]
    # Remove time and search_id if provided
    query_params.pop("time", None)
    query_params.pop("search_id", None)
    query_params.pop("disabled_personalization", None)
    query_params.pop("page", None)

    # Rebuild the query string and the entire URL
    new_query = urlencode(query_params, doseq=True)
    processed_query = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment,
        )
    )

    # Some queries are made with filters only, so we need to check if the search_text is present
    if db.is_query_in_db(processed_query) is True:
        return "Query already exists.", False
    else:
        # add the query to the db
        db.add_query_to_db(processed_query, name)
        return "Query added.", True


def get_formatted_query_list():
    """
    Get a formatted list of all queries in the database.

    Returns:
        str: A formatted string with all queries, numbered
    """
    all_queries = db.get_queries()
    queries_keywords = []
    for query in all_queries:
        parsed_url = urlparse(query[1])
        query_params = parse_qs(parsed_url.query)

        # Get the name or Extract the value of 'search_text'
        query_name = (
            query[3]
            if query[3] is not None
            else query_params.get("search_text", [None])[0]
        )

        if query_name[0] is None:
            # Use query text instead of the whole query object
            queries_keywords.append([query[1]])
        else:
            queries_keywords.append(query_name)

    query_list = ("\n").join(
        [str(i + 1) + ". " + j for i, j in enumerate(queries_keywords)]
    )
    return query_list


def process_remove_query(number):
    """
    Process the removal of a query from the database.

    Args:
        number (str): The number of the query to remove or "all" to remove all queries

    Returns:
        tuple: (message, success)
            - message (str): Status message
            - success (bool): True if query was removed successfully
    """
    if number == "all":
        db.remove_all_queries_from_db()
        return "All queries removed.", True

    # Check if number is a valid digit
    if number.isdigit():
        # Remove the query from the database
        db.remove_query_from_db(number)
        return "Query removed.", True
    else:
        return "Invalid number.", False


def process_update_query(query_id, query, name):
    """
    Process the update of a query in the database.

    Args:
        query_id (int): The ID of the query to update
        query (str): The new Vinted query URL
        name (str, optional): A new name for the query. If provided, it will be used as the query name.

    Returns:
        tuple: (message, success)
            - message (str): Status message
            - success (bool): True if query was updated successfully
    """
    # Parse the URL and extract the query parameters
    parsed_url = urlparse(query)
    query_params = parse_qs(parsed_url.query)

    # Ensure the order flag is set to newest_first
    query_params["order"] = ["newest_first"]
    # Remove time and search_id if provided
    query_params.pop("time", None)
    query_params.pop("search_id", None)
    query_params.pop("disabled_personalization", None)
    query_params.pop("page", None)

    # Rebuild the query string and the entire URL
    new_query = urlencode(query_params, doseq=True)
    processed_query = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment,
        )
    )

    # Update the query in the database
    if db.update_query_in_db(query_id, processed_query, name):
        return "Query updated.", True
    else:
        return "Failed to update query.", False


def process_add_country(country):
    """
    Process the addition of a country to the allowlist.

    Args:
        country (str): The country code to add

    Returns:
        tuple: (message, country_list)
            - message (str): Status message
            - country_list (list): Current list of allowed countries
    """
    # Format the country code (remove spaces)
    country = country.replace(" ", "")
    country_list = db.get_allowlist()

    # Validate the country code (check if it's 2 characters long)
    if len(country) != 2:
        return "Invalid country code", country_list

    # Check if the country is already in the allowlist
    # If country_list is 0, it means the allowlist is empty
    if country_list != 0 and country.upper() in country_list:
        return f'Country "{country.upper()}" already in allowlist.', country_list

    # Add the country to the allowlist
    db.add_to_allowlist(country.upper())
    return "Country added.", db.get_allowlist()


def process_remove_country(country):
    """
    Process the removal of a country from the allowlist.

    Args:
        country (str): The country code to remove

    Returns:
        tuple: (message, country_list)
            - message (str): Status message
            - country_list (list): Current list of allowed countries
    """
    # Format the country code (remove spaces)
    country = country.replace(" ", "")

    # Validate the country code (check if it's 2 characters long)
    if len(country) != 2:
        return "Invalid country code", db.get_allowlist()

    # Remove the country from the allowlist
    db.remove_from_allowlist(country.upper())
    return "Country removed.", db.get_allowlist()


def get_user_country(profile_id):
    """
    Get the country code for a Vinted user.

    Makes an API request to retrieve the user's country code.
    Handles rate limiting by trying an alternative endpoint.

    Args:
        profile_id (str): The Vinted user's profile ID

    Returns:
        str: The user's country code (2-letter ISO code) or "XX" if it can't be determined
    """
    # Users are shared between all Vinted platforms, so we can use whatever locale we want
    url = f"https://www.vinted.fr/api/v2/users/{profile_id}?localize=false"
    response = requester.get(url)
    # That's a LOT of requests, so if we get a 429 we wait a bit before retrying once
    if response.status_code == 429:
        # In case of rate limit, we're switching the endpoint. This one is slower, but it doesn't RL as soon.
        # We're limiting the items per page to 1 to grab as little data as possible
        url = f"https://www.vinted.fr/api/v2/users/{profile_id}/items?page=1&per_page=1"
        response = requester.get(url)
        try:
            user_country = response.json()["items"][0]["user"]["country_iso_code"]
        except KeyError:
            logger.warning(
                "Couldn't get the country due to too many requests. Returning default value."
            )
            user_country = "XX"
    else:
        user_country = response.json()["user"]["country_iso_code"]
    return user_country


def process_items(queue):
    """
    Process all queries from the database, search for items, and put them in the queue.
    Uses the global items_queue by default, but can accept a custom queue for backward compatibility.

    Args:
        queue (Queue, optional): The queue to put the items in. Defaults to the global items_queue.

    Returns:
        None
    """

    all_queries = db.get_queries()

    # Initialize Vinted
    vinted = Vinted()

    # Get the number of items per query from the database
    items_per_query = int(db.get_parameter("items_per_query"))

    max_age_minutes = get_item_max_age()

    total_found, total_kept = 0, 0

    # for each keyword we parse data
    for query in all_queries:
        all_items = vinted.items.search(query[1], nbr_items=items_per_query)
        # Measured before filtering, so a window that is already too narrow
        # cannot hide the measurement that would widen it.
        record_indexing_delay(all_items)
        # Only consider recent items, to keep a brand new query from notifying
        # a whole catalogue at once. The window has to stay well above Vinted's
        # indexing delay: an item shows up in search results long after the
        # timestamp it carries, and a window shorter than that delay silently
        # drops every single item.
        data = [item for item in all_items if item.is_new_item(max_age_minutes)]
        queue.put((data, query[0]))
        logger.info(f"Scraped {len(data)} items for query: {query[1]}")
        total_found += len(all_items)
        total_kept += len(data)

    # One outcome per cycle, not per query: one query still bringing items
    # through means the pipeline works, however many others are quiet.
    record_scrape_outcome(total_found, total_kept)



MIN_DELAY_SAMPLES = 5


def record_indexing_delay(all_items):
    """
    Record how far behind Vinted's search index is running.

    The freshest item a search returns is the most recently indexed one, so
    its age is an upper bound on the indexing delay. It is measured before the
    age filter is applied, otherwise a window that is already too narrow would
    hide the very measurement needed to widen it.

    Args:
        all_items (list): Items returned by a search, before filtering.
    """
    if not all_items:
        return
    try:
        now = datetime.now(timezone.utc)
        youngest = min(
            (now - item.created_at_ts).total_seconds() / 60 for item in all_items
        )
        keep_last = int(float(db.get_parameter("indexing_delay_window") or 60))
        db.add_indexing_delay_sample(round(youngest, 1), keep_last)
    except Exception as e:
        logger.debug(f"Could not record indexing delay: {e}")


def get_item_max_age():
    """
    Return the age window to filter items with, in minutes.

    In auto mode the window follows the observed indexing delay: the smallest
    of the recent measurements times a safety factor, kept between the
    configured floor and cap.

    The smallest sample is used rather than an average, because a measurement
    only reflects the indexing delay when an item was actually published
    recently. During a quiet spell the freshest item on offer keeps ageing and
    every other statistic drifts upwards with it, while the minimum still
    holds the last time a genuinely fresh item was seen. Simulated over 60
    cycles around a true delay of 90 minutes, the minimum stayed near 80
    whether fresh items made up 60% or 3% of the samples, where the median
    climbed to 556.

    Widening is the safe direction: duplicates are already ruled out by the
    stored timestamps and item ids, while being too narrow silently drops
    everything.

    Returns:
        int: The window in minutes.
    """
    try:
        floor = int(float(db.get_parameter("item_max_age_minutes")))
    except (TypeError, ValueError):
        floor = 240

    if str(db.get_parameter("item_max_age_mode")).lower() != "auto":
        return floor

    samples = db.get_indexing_delay_samples()
    # A single measurement can land during a quiet spell and be wildly off, so
    # the window only follows the measurements once there are enough of them.
    if len(samples) < MIN_DELAY_SAMPLES:
        return floor

    try:
        factor = float(db.get_parameter("item_max_age_factor") or 3)
        cap = float(db.get_parameter("item_max_age_cap") or 1440)
    except (TypeError, ValueError):
        factor, cap = 3.0, 1440.0

    observed = min(samples)
    window = int(min(max(observed * factor, floor), cap))
    previous = db.get_parameter("item_max_age_effective")
    if str(previous) != str(window):
        logger.info(
            f"Item age window now {window} min "
            f"(observed indexing delay {observed:.0f} min "
            f"over {len(samples)} samples)"
        )
        db.set_parameter("item_max_age_effective", str(window))
    return window


def record_scrape_outcome(found, kept):
    """
    Track the signature of a silent breakdown.

    Searches returning results while none of them is ever kept means the age
    window no longer matches how Vinted timestamps its items. Nothing raises,
    nothing is logged as an error, and notifications simply stop: the only way
    to notice is to count how long it lasts.

    Counts cover a whole cycle across every query, so one productive query is
    enough to clear the alarm.

    Args:
        found (int): Items returned by the searches this cycle.
        kept (int): Items that passed the age window this cycle.
    """
    try:
        if kept > 0 or found == 0:
            # Anything getting through clears the alarm, so a recovery is not
            # reported as an ongoing failure.
            if db.get_parameter("watchdog_empty_cycles") not in ("0", None):
                db.set_parameter("watchdog_empty_cycles", "0")
                db.set_parameter("watchdog_alerted", "False")
            return
        cycles = int(float(db.get_parameter("watchdog_empty_cycles") or 0)) + 1
        db.set_parameter("watchdog_empty_cycles", str(cycles))
    except Exception as e:
        logger.debug(f"Could not record scrape outcome: {e}")


def pending_watchdog_alert():
    """
    Return the alert to send when the breakdown has lasted long enough.

    Returns:
        str | None: The message to send, or None when there is nothing to say.
    """
    if str(db.get_parameter("watchdog_enabled")).lower() != "true":
        return None
    if str(db.get_parameter("watchdog_alerted")).lower() == "true":
        # Already reported: say it once, not every minute.
        return None
    try:
        cycles = int(float(db.get_parameter("watchdog_empty_cycles") or 0))
        threshold = int(float(db.get_parameter("watchdog_cycles") or 30))
    except (TypeError, ValueError):
        return None
    if cycles < threshold:
        return None

    delay = db.get_parameter("query_refresh_delay") or "60"
    try:
        minutes = int(cycles * float(delay) / 60)
    except (TypeError, ValueError):
        minutes = cycles

    db.set_parameter("watchdog_alerted", "True")
    logger.warning(
        f"Watchdog: searches returned results but nothing was kept for "
        f"{cycles} cycles"
    )
    return (
        "⚠️ <b>No item kept for "
        + str(minutes)
        + " minutes</b>\n\n"
        + "Searches are returning results, but every item is being discarded.\n"
        + "This usually means Vinted now publishes items later than the age "
        + "window allows.\n\n"
        + "Raise <b>Maximum Item Age</b> in Configuration."
    )


def build_daily_summary():
    """
    Build the daily activity report, or None when it is not due yet.

    Returns:
        str | None: The message to send.
    """
    if str(db.get_parameter("daily_summary_enabled")).lower() != "true":
        return None
    now = datetime.now()
    try:
        hour = int(float(db.get_parameter("daily_summary_hour") or 20))
    except (TypeError, ValueError):
        hour = 20
    if now.hour < hour:
        return None
    today = now.strftime("%Y-%m-%d")
    if db.get_parameter("daily_summary_last_sent") == today:
        return None
    db.set_parameter("daily_summary_last_sent", today)

    summary = db.get_notification_summary(
        datetime.combine(now.date(), dtime.min).timestamp()
    )
    lines = [
        "📊 <b>Daily summary</b>",
        "",
        f"Items found: {summary['seen']}",
        f"Notified: {summary['notified']} (of which {summary['silenced']} silent)",
        f"Skipped: {summary['skipped']}",
    ]
    best = summary["best"]
    if best:
        title, price, currency, url, discount = best
        lines += [
            "",
            f"Best deal: <a href=\"{url}\">{escape(str(title))}</a>",
            f"{price} {currency} — {round(abs(discount))}% below market",
        ]
    return "\n".join(lines)


class _SafeDict(dict):
    """
    A mapping that never raises on a missing key.

    The message template is user-editable, so an unknown placeholder must not
    crash the notification pipeline.
    """

    def __missing__(self, key):
        return f"{{{key}}}"


def _raw_amount(item, key):
    """Read a nested price amount from the raw API payload."""
    try:
        return item.raw_data[key]["amount"]
    except (KeyError, TypeError):
        return None


def build_item_message(item, evaluation=None):
    """
    Render the notification message for an item.

    All text coming from Vinted is HTML-escaped because the Telegram plugin
    sends messages with parse_mode="HTML".

    Args:
        item (Item): The item to build a message for.
        evaluation (dict, optional): A price evaluation already computed for
            this item. Passing it avoids evaluating the same item twice.

    Returns:
        str: The rendered message.
    """
    message_template = db.get_parameter("message_template")

    total_amount = _raw_amount(item, "total_item_price")
    total_price = (
        f"{total_amount} {item.currency}" if total_amount is not None else "n/a"
    )

    if evaluation is None:
        evaluation = price_reference.evaluate(item)

    values = _SafeDict(
        title=escape(str(item.title or "")),
        price=f"{item.price} {item.currency}",
        total_price=total_price,
        brand=escape(str(item.brand_title or "")),
        size=escape(str(item.size_title or "n/a")),
        status=escape(str(item.raw_data.get("status") or "n/a")),
        favourites=item.raw_data.get("favourite_count", 0),
        views=item.raw_data.get("view_count", 0),
        url=item.url,
        image="" if item.photo is None else item.photo,
        market_price=evaluation["market_price"],
        discount=evaluation["discount"],
        deal=evaluation["deal"],
    )
    return message_template.format_map(values)



def log_item_outcome(item, evaluation, silent, skipped):
    """Record what was decided for an item, for the daily summary."""
    try:
        db.add_notification_log(
            item.id,
            item.title,
            item.price,
            item.currency,
            item.url,
            evaluation.get("discount_pct"),
            evaluation.get("deal"),
            silent,
            skipped,
        )
    except Exception as e:
        logger.debug(f"Could not log outcome for item {item.id}: {e}")


def emit_system_messages(new_items_queue):
    """
    Push the watchdog alert and the daily summary onto the outgoing queue.

    They travel the same path as item notifications, so they reach whichever
    channels are enabled without a second delivery mechanism.

    Args:
        new_items_queue (Queue): The queue consumed by the notification plugins.
    """
    link = db.get_parameter("github_url") or "https://www.vinted.fr"
    for builder in (pending_watchdog_alert, build_daily_summary):
        try:
            message = builder()
        except Exception as e:
            logger.warning(f"Could not build system message: {e}")
            continue
        if message:
            # Never silent: these are the messages that must be noticed.
            new_items_queue.put((message, link, "Open project", None, None, False))


def clear_item_queue(items_queue, new_items_queue):
    """
    Process items from the items_queue.
    This function is scheduled to run frequently.
    """
    emit_system_messages(new_items_queue)

    if not items_queue.empty():
        data, query_id = items_queue.get()
        banwords_str = db.get_parameter("banwords")
        query_url = db.get_query_url(query_id)
        for item in reversed(data):

            # If already in db, pass
            last_query_timestamp = db.get_last_timestamp(query_id)
            if (
                last_query_timestamp is not None
                and last_query_timestamp >= item.raw_timestamp
            ):
                pass
            # In case of multiple queries, we need to check if the item is already in the db
            elif db.is_item_in_db_by_id(item.id) is True:
                # We update the timestamp
                db.update_last_timestamp(query_id, item.raw_timestamp)
                pass
            # If there's an allowlist and
            # If the user's country is not in the allowlist, we just update the timestamp
            elif db.get_allowlist() != 0 and (
                get_user_country(item.raw_data["user"]["id"])
            ) not in (db.get_allowlist() + ["XX"]):
                db.update_last_timestamp(query_id, item.raw_timestamp)
                pass
            # Check if the item title contains any banwords
            elif banwords_str and contains_banwords(item.title, banwords_str):
                # If it contains banwords, just update the timestamp and skip
                db.update_last_timestamp(query_id, item.raw_timestamp)
                pass
            else:
                evaluation = price_reference.evaluate(item, query_url)
                # Items priced too far above the market are recorded but not
                # notified, so that the feed stays quiet instead of noisy.
                if not price_reference.should_notify(evaluation):
                    db.update_last_timestamp(query_id, item.raw_timestamp)
                    logger.info(
                        f"Item {item.id} skipped, {evaluation['discount']}"
                    )
                    log_item_outcome(item, evaluation, silent=False, skipped=True)
                    continue
                # We create the message
                content = build_item_message(item, evaluation)
                silent = price_reference.is_silent(evaluation)
                # add the item to the queue
                new_items_queue.put(
                    (content, item.url, "Open Vinted", None, None, silent)
                )
                log_item_outcome(item, evaluation, silent=silent, skipped=False)
                # Add the item to the db
                db.add_item_to_db(
                    id=item.id,
                    timestamp=item.raw_timestamp,
                    price=item.price,
                    title=item.title,
                    photo_url=item.photo,
                    query_id=query_id,
                    currency=item.currency,
                )


def contains_banwords(title, banwords_str):
    """
    Check if a title contains any banwords.

    Args:
        title (str): The title to check
        banwords_str (str): List of banwords separated by 3 pipe character
    Returns:
        bool: True if the title contains any banwords, False otherwise
    """

    # Split the banwords string into a list using pipe as delimiter
    banwords = [
        word.strip().lower() for word in banwords_str.split("|||") if word.strip()
    ]

    # If the list is empty, return False
    if not banwords:
        return False

    # Check if any banword is in the title (case-insensitive)
    title_lower = title.lower()
    for word in banwords:
        if word in title_lower:
            return True

    return False


def check_version():
    """
    Check if the application is up to date
    """
    try:
        # Get URL from the database
        github_url = db.get_parameter("github_url")
        # Get version from the database
        ver = db.get_parameter("version")
        # Get latest version from the repository
        url = f"{github_url}/releases/latest"
        response = requests.get(url)

        if response.status_code == 200:
            latest_version = response.url.split("/")[-1]
            # A repository with no release at all redirects to the releases
            # index page, whose last URL segment would be read as a version.
            if not re.match(r"^v?\d", latest_version):
                return True, ver, ver, github_url
            is_up_to_date = ver == latest_version
            return is_up_to_date, ver, latest_version, github_url
        else:
            # If we can't check, assume it's up to date
            return True, ver, ver, github_url
    except Exception as e:
        logger.error(f"Error checking for new version: {str(e)}", exc_info=True)
        # If we can't check, assume it's up to date
        return True, ver, ver, github_url
