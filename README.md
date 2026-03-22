## BOE Judicial Edictos Scraper

Scraper for judicial edicts published in the Spanish BOE.

On one occasion, I was not properly notified of a court document, so I decided to develop a program that would scrape the BOE(Spanish Official State Gazette) on a daily basis to check whether my name appeared in it.

Since 01 June of 2025, I download all the "Edictos" and stored them in my local DB. You can use this repo to scrape for now on or contact me to get infor from the past.

- [BOE Judicial Edictos Scraper](#boe-judicial-edictos-scraper)
  - [What this project does](#what-this-project-does)
  - [Requirements](#requirements)
  - [Typical commands](#typical-commands)
  - [Core CLI](#core-cli)
  - [Python API](#python-api)
  - [Configuration via environment variables](#configuration-via-environment-variables)


### What this project does

- **Scrape BOE judicial edicts by date**
  - Hits `https://www.boe.es` for one or many calendar dates.
  - Filters edicts whose HTML matches a user-supplied regular expression.
- **Extract structured records**
  - **Fields**: `occurrence`, `date`, `reference_id`, `department`.
  - **Sources**:
    - Online spider: `src/boe_scraper/spiders/boe_parser.py`.
- **Write data in analytics-friendly formats**
  - **CSV file** (single file, append across dates).
  - **Delta Lake table** (directory).

---

### Requirements

- **Python**: `>=3.14`.
- **uv**: uv deps manager installed.
- **Runtime expectations**
  - Run commands from the project root (where `scrapy.cfg` and `pyproject.toml` live).
  - Have network access to `www.boe.es` for online scraping.

---

### Typical commands

```bash
# Scrape the current month to a CSV
uv run boe_scraper/runner.py edictos\
  --output-path data/boe_edicts.csv \
  --pattern "(JUZGADO DE LO SOCIAL.*)"


# Scrape specific dates and save HTML locally
uv run boe_scraper/runner.py edictos \
  --dates 2025-06-02 2025-06-03 2025-06-09 \
  --output-path data/boe_edicts.csv \
  --download-path ./downloads \
  --store-html \
  --pattern "(JUZGADO DE LO SOCIAL.*)"
```

---

### Core CLI

`boe_scraper/runner.py` is the main entrypoint for hitting BOE and writing results.

**edictos*: command to scrape edictos judiciales section of BOE.

- **Required arguments**
  - **`--output-path PATH`**: where to write data.
  - **`--pattern REGEX`**: Python regular expression applied to each edict HTML.
    - The match determines the `occurrence` field.
    - If there is no match, the edict is skipped.

- **Date selection (pick exactly one mode, otherwise defaults to current month)**
  - **Explicit dates**
    - `--dates YYYY-MM-DD [YYYY-MM-DD ...]`
  - **Date range (inclusive)**
    - `--start-date YYYY-MM-DD --end-date YYYY-MM-DD`
  - **Specific month**
    - `--month M [--year YYYY]`
    - Year defaults to the current year if omitted.
  - **Weeks from a start date**
    - `--start-date YYYY-MM-DD --weeks N`
  - **Previous calendar week**
    - `--previous-week`
  - **No date arguments**
    - Uses all days in the current month.

- **Output format**
  - **`--format csv`** (default): write a single CSV file.
  - **`--format delta`**: write/append to a Delta table directory.

- **HTML storage and logging**
  - **`--download-path PATH`**
    - Overrides `DOWNLOAD_PATH` (see environment variables below).
  - **`--store-html`**
    - Intended to control persistence of raw HTML files under `DOWNLOAD_PATH`.
    - HTML is written into `DOWNLOAD_PATH/date=YYYY-MM-DD/REFERENCE_ID.html`.
  - **`--log-file file`**
    - Overrides `LOG_FILE`.
  - **`--log-level LEVEL`**
    - Overrides `LOG_LEVEL` (e.g. `INFO`, `DEBUG`).


### Python API

The same date-generation and runner logic can be used programmatically.

- **From `boe_scraper/runner.py`**
  - **`scrape_current_month(parse_only: bool = False, pattern: str | None = None)`**
  - **`scrape_last_week(parse_only: bool = False, pattern: str | None = None)`**
  - **`scrape_previous_week(parse_only: bool = False, pattern: str | None = None)`**
  - **`scrape_specific_month(year: int, month: int, parse_only: bool = False, pattern: str | None = None)`**
  - **`scrape_date_range(start_date: str, end_date: str, parse_only: bool = False, pattern: str | None = None)`**

- **Example**

```python
from boe_scraper.runner import scrape_date_range

results = scrape_date_range(
    start_date="2025-06-01",
    end_date="2025-06-10",
    parse_only=False,
    pattern=r"(JUZGADO DE LO SOCIAL.*)",
)

print(results["successful_parses"], "dates parsed successfully")
```

---

### Configuration via environment variables

- **`DOWNLOAD_PATH`**
  - Default: `./downloads`.
  - Used as base directory for HTML storage and offline re-parsing.
- **`LOG_FILE`**
  - Default: `./logs/boe_scraper.log`.
  - Directory where log files are written.
- **`LOG_LEVEL`**
  - Default: `INFO`.
  - Logging verbosity for both runners.

CLI options (`--download-path`, `--log-path`, `--log-level`) override these defaults for the current run only.

