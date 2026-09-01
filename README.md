# Vinted Deal Hunter

A real-time notification system for Vinted listings that works across all Vinted country domains. Get instant alerts
when items matching your search criteria are posted, and know straight away whether the price is worth it.

Vinted exposes no retail price, so this project builds a **market reference** from Vinted itself and scores every
listing against it. See [Deal Detection](#-deal-detection).

> Fork of [Fuyucch1/Vinted-Notifications](https://github.com/Fuyucch1/Vinted-Notifications), extended with market
> price references and deal scoring.

![Vinted-Notifications](https://github.com/user-attachments/assets/f2788511-5a8a-4a8d-8198-a4135081a3d8)

---

## ⚡ Quickstart

If you just want to get started fast with Docker Compose:

```bash
git clone https://github.com/playm8/vinted-deal-hunter.git
cd vinted-deal-hunter
docker compose up -d --build
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 📋 Features

- **Web UI**: Manage everything through an intuitive web interface
- **Multi-Country Support**: Works on all Vinted domains regardless of country
- **Real-Time Notifications**: Get instant alerts for new listings
- **Multiple Search Queries**: Monitor multiple search terms simultaneously
- **Country Filtering**: Filter items by seller's country of origin
- **RSS Feed**: Subscribe to your search results with any RSS reader
- **Telegram Integration**: Receive notifications directly in Telegram

---

## 💰 Deal Detection

Vinted exposes no retail price, so the **market reference** is built from
Vinted itself: for every new item, it searches the catalog for comparable
listings (same brand, same significant title keywords, same size), takes the
**median** of their prices and compares it with the item price.

The notification then shows whether the listing is worth it:

```
🆕 Air max 95 bianche
💶 60.0 EUR  (total 63.7 EUR)
📊 Market ref : 106.50 EUR  (-44% vs market)
✅ Good deal (based on 18 listings)
🛍️ Nike · 📏 44 · ✨ Neuf sans étiquette
❤️ 26  👁️ 0
```

### New message template variables

| Variable | Description |
| --- | --- |
| `{total_price}` | Price including the buyer protection fee |
| `{status}` | Condition declared by the seller (e.g. "Neuf avec étiquette") |
| `{size}` | Item size |
| `{favourites}` / `{views}` | Engagement counters |
| `{url}` | Item URL |
| `{market_price}` | Median price of comparable listings |
| `{discount}` | Gap with the market reference (positive means more expensive) |
| `{deal}` | Verdict: 🔥 excellent, ✅ good, ➖ fair, ⚠️ above market |

Unknown placeholders are left as-is instead of breaking the notification, and
all Vinted text is HTML-escaped before being sent to Telegram.

### Interface language

The web interface is available in English and French, switchable from
Configuration → System Settings → Language. English strings are used as
translation keys, so an untranslated string falls back to English instead of
showing a placeholder. Adding a language means adding one entry to
`LANGUAGES` and one dictionary to `TRANSLATIONS` in
`web_ui_plugin/translations.py`; nothing else has to change.

### Monitoring

A notifier that goes quiet is worse than one that fails loudly: Vinted publishes items in its search results long
after the timestamp they carry, and when that delay grows past the age window every item is discarded, with no error
anywhere. The watchdog watches for exactly that signature — searches returning results while nothing is ever kept —
and warns after `watchdog_cycles` consecutive cycles. It reports once, and re-arms as soon as an item gets through.

A daily summary reports what was found, notified, silenced and skipped, plus the best deal of the day. It doubles as a
heartbeat: receiving it means the pipeline ran.

| Parameter | Default | Description |
| --- | --- | --- |
| `watchdog_enabled` | `True` | Warn when searches return results but nothing is kept |
| `watchdog_cycles` | `30` | Consecutive empty cycles to tolerate before warning |
| `daily_summary_enabled` | `True` | Send one summary a day |
| `daily_summary_hour` | `20` | Hour of the day, server time |
| `item_max_age_minutes` | `240` | Ignore items older than this, and the floor of the automatic window |
| `item_max_age_mode` | `auto` | Follow the measured indexing delay, or stay on the fixed value |
| `item_max_age_cap` | `1440` | Upper bound the automatic window never exceeds |
| `notification_log_retention_days` | `30` | How long per-item outcomes are kept |

### Adaptive age window

Vinted publishes an item in its search results long after the timestamp the item carries, and that delay moves. A
window shorter than the delay discards every item, silently. In auto mode the window measures the delay instead of
assuming it: the freshest item each search returns is the most recently indexed one, so its age bounds the delay. The
measurement is taken **before** the age filter, otherwise a window that is already too narrow would hide the very
measurement needed to widen it.

The window is the **smallest** recent measurement times a safety factor, kept between the floor and the cap. The
minimum is used rather than an average because a measurement only reflects the indexing delay when an item was
actually published recently; during a quiet spell the freshest item on offer keeps ageing and every other statistic
drifts up with it. Simulated over 60 cycles around a true delay of 90 minutes, the minimum stayed near 80 whether
fresh items made up 60% or 3% of the samples, where the median climbed to 556.

Widening is the safe direction: duplicates are ruled out by the stored timestamps and item ids, so a window wider than
necessary costs nothing, while a narrow one drops everything without a word.

### Settings (Configuration → Deal Detection)

| Parameter | Default | Description |
| --- | --- | --- |
| `price_reference_enabled` | `True` | Turn the feature off to keep the original behaviour |
| `price_reference_sample_size` | `20` | Listings fetched per comparison |
| `price_reference_min_samples` | `5` | Below this, no reference is shown |
| `price_reference_ttl_hours` | `24` | How long a reference price is cached |
| `deal_threshold_good` | `25` | Discount (%) for ✅ |
| `deal_threshold_hot` | `50` | Discount (%) for 🔥 |
| `price_reference_max_dispersion` | `80` | Above this price spread, no verdict is announced |
| `price_history_retention_days` | `90` | How long past references are kept for the trends table |
| `notify_silent_below` | `25` | Below this discount, the notification arrives without a sound |
| `notify_skip_below` | *(empty)* | Below this discount, nothing is sent at all. `0` drops anything above market price |

Comparables are restricted to the item's condition group whenever enough of them share it, prices outside 1.5
interquartile ranges are discarded as unrelated products, and a reference whose prices are too scattered announces no
verdict at all rather than a misleading one.

**Narrow your queries to a category.** When a monitored query carries a Vinted category filter, the comparison stays
inside that category instead of drifting to accessories of the same brand, and the query list flags the ones that do
not. Measured on the same listings, a category-restricted comparison cut the average price spread from 66% to 52%;
one pair of trainers moved from an unusable reference (median 30 EUR, spread 109%) to a reliable one (median 110 EUR,
spread 42%).

Titles are tokenised with stopwords for English, French, Italian, German, Spanish, Dutch and Polish, since listings
from every Vinted country show up in a single country's search results.

Past references are kept in `price_reference_history` and summarised per brand on the dashboard, so a brand getting
cheaper or more expensive becomes visible over time. Entries older than the retention window are dropped at startup.

Items with no market reference are never silenced nor skipped: not knowing a price is not a reason to hide a
listing.

Each new item costs one extra catalog request, cached per
(domain, brand, keywords, size), so a burst of similar items only queries once.

---

## 📦 Installation

### Option 1: Docker Compose (Recommended)

#### Prerequisites

- Docker and Docker Compose installed on your system
- Telegram bot token (for Telegram notifications)

#### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/playm8/vinted-deal-hunter.git
   cd vinted-deal-hunter
   ```

2. **Build and start the container**

   ```bash
   docker compose up -d --build
   ```

   The shipped `docker-compose.yml` builds the image from these sources. There is no prebuilt image on Docker Hub:
   the deal detection lives in this repository, so the image has to be built from it.

   > **Note**: The compose file uses named volumes (`VN_data` and `VN_logs`) managed by Docker, so your database and
   logs survive a container removal or rebuild.

3. **Access the Web UI**

   Once started, access the Web UI at [http://localhost:8000](http://localhost:8000) to complete the setup.

### Option 2: Docker Run

#### Prerequisites

- Docker installed on your system
- Telegram bot token (for Telegram notifications)

#### Setup

1. **Build the image and create directories for persistent data**

   ```bash
   git clone https://github.com/playm8/vinted-deal-hunter.git
   cd vinted-deal-hunter
   docker build -t vinted-deal-hunter .
   mkdir -p data logs
   ```

2. **Run the container**

   ```bash
   docker run -d \
     --name vinted-deal-hunter \
     -p 8000:8000 \
     -p 8080:8080 \
     -v "$(pwd)/data:/app/data" \
     -v "$(pwd)/logs:/app/logs" \
     --restart unless-stopped \
     vinted-deal-hunter
   ```

   > **Note**: The volume mounts ensure your data and logs are preserved even if the container is removed or updated.
   The database is stored in the `data` directory, and logs are stored in the `logs` directory.

3. **Access the Web UI**

   Once started, access the Web UI at [http://localhost:8000](http://localhost:8000) to complete the setup.

### Option 3: Self-Build

#### Prerequisites

- Python 3.11 or higher
- Telegram bot token (for Telegram notifications)

#### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/playm8/vinted-deal-hunter.git
   cd vinted-deal-hunter
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Initial Configuration**

   The application can be configured through the Web UI after starting. However, you can also change the Web UI port in
   the
   `configuration_values.py` file directly.

4. **Run the application**

   ```bash
   python vinted_notifications.py
   ```

   Once started, access the Web UI at [http://localhost:8000](http://localhost:8000) to complete the setup.

---

## 🚀 Usage

### Web UI

The Web UI is the easiest way to manage the application. Access it at [http://localhost:8000](http://localhost:8000)
after starting the application.

Features available in the Web UI:

- **Dashboard**: Overview of application status and recent items
- **Queries Management**: Add, remove, and view search queries
- **Items Viewing**: Browse and filter items found by the application
- **Allowlist Management**: Filter items by seller's country
- **Configuration**: Set up Telegram bot, RSS feed, and other settings
- **Logs**: View application logs directly from the web interface

### Telegram Commands

After configuring your Telegram bot in the Web UI, you can use the following commands:

- `/add_query query` - Add a search query to monitor
- `/remove_query query_number` - Remove a specific query
- `/remove_query all` - Remove all queries
- `/queries` - List all active queries
- `/hello` - Check if the bot is working
- `/create_allowlist` - Create a country allowlist (will slow down processing)
- `/delete_allowlist` - Delete the country allowlist
- `/add_country XX` - Add a country to the allowlist (ISO3166 format)
- `/remove_country XX` - Remove a country from the allowlist
- `/allowlist` - View the current allowlist

### Query Examples

Queries must be added with a whole link. It works with filters.:

   ```
   /add_query https://www.vinted.fr/catalog?search_text=nike%20shoes&price_to=50&currency=EUR&brand_id[]=53
   ```

### RSS Feed

The RSS feed provides an alternative way to receive notifications. After enabling it in the Web UI, access it
at [http://localhost:8080](http://localhost:8080).

## ⚙️ Advanced Configuration

### Proxy Support

The application supports using proxies to avoid rate limits. Those are configured in the configuration tab of the Web
UI.

### Custom Notification Format

You can customize the notification message format:

```python
MESSAGE = '''\
🆕 Title: {title}
💶 Price: {price}
🛍️ Brand: {brand}
<a href='{image}'>&#8205;</a>
'''
```

## 🔄 Updating

Database migrations run automatically on startup, so an update never requires manual SQL. Your database lives in a
volume (or in `data/`) and is left untouched by a rebuild.

### Docker Compose

```bash
git pull
docker compose up -d --build
```

### Docker Run

```bash
git pull
docker build -t vinted-deal-hunter .
docker stop vinted-deal-hunter && docker rm vinted-deal-hunter
# then run the container again with the same command as in the installation section
```

### Self-Build

```bash
git pull
pip install -r requirements.txt
```

Then restart the application.

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

Or without installing anything locally:

```bash
docker compose run --rm --entrypoint sh vinted-deal-hunter -c "pip install -q pytest && python -m pytest tests/ -q"
```

The suite covers the logic that decides what you get notified about: keyword
extraction across languages, outlier filtering, condition grouping, the
silent and skip thresholds, message rendering and escaping, the watchdog, and
the adaptive age window. No test touches the network.

Each test runs against a real SQLite database built the way a fresh install
builds it — the initial schema, then every migration in version order — so
the migration chain is exercised on every run.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the [GNU AFFERO GENERAL PUBLIC LICENSE](LICENSE), inherited from the upstream
project it forks.

Changes made in this fork: market price reference and deal scoring, enriched notification fields, HTML escaping of
Vinted text, and tolerant message template rendering.

## 🙏 Acknowledgements

- Thanks to [@Fuyucch1](https://github.com/Fuyucch1) for [Vinted-Notifications](https://github.com/Fuyucch1/Vinted-Notifications), the upstream project this fork is built on.
- Thanks to [@herissondev](https://github.com/herissondev) for maintaining pyVinted, a core dependency of this project.
