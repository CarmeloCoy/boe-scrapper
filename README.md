## BOE Scraper

Scraper for some elements published in the Spanish BOE:
 - Implemented for udicial edicts and BOE auctions (subastas).

On one occasion, I was not properly notified of a court document, so I decided to develop a program that would scrape the BOE (Spanish Official State Gazette) daily to check whether my name appeared in it.

Since 01 June 2025, I have downloaded all the "Edictos" and stored them in my local DB. You can use this repo to scrape from now on, or contact me to get information from past data.

- [BOE Scraper](#boe-scraper)
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
- **Scrape BOE auctions (subastas)**
  - Hits `https://subastas.boe.es` and filters by province.
  - Supports optional start-date range filters.
- **Extract structured records**
  - **Edictos fields**: `occurrence`, `date`, `reference_id`, `department`.
  - **Subastas fields**: auction metadata, authority information, documents, images, and assets.
  - **Sources**:
    - Online spider (edictos): `boe_scraper/scrapy/spiders/boe_parser.py`.
    - Online spider (subastas): `boe_scraper/scrapy/spiders/subastas_boe_parser.py`.
- **Write data in different formats**
  - **CSV file**
  - **JSONL file**

---

### Requirements

- **Python**: `>=3.14`.
- **uv**: uv deps manager installed.
- **Runtime expectations**
  - Run commands from the project root (where `scrapy.cfg` and `pyproject.toml` live).
  - Have network access to `www.boe.es` and `subastas.boe.es` for online scraping.

---

### Typical commands

```bash
# Scrape edictos for the current month to CSV
uv run boe_scraper/entrypoint.py edictos \
  --output-path data/boe_edictos.csv \
  --pattern "(JUZGADO DE LO SOCIAL.*)"


# Scrape edictos for specific dates and save HTML locally
uv run boe_scraper/entrypoint.py edictos \
  --dates 2025-06-02 2025-06-03 2025-06-09 \
  --output-path data/boe_edictos.csv \
  --download-path ./downloads \
  --store-html \
  --pattern "(JUZGADO DE LO SOCIAL.*)"

# Scrape subastas for one province and date range
uv run boe_scraper/entrypoint.py subastas \
  --cod-provincia 30 \
  --from-start-date 2026-01-01 \
  --to-start-date 2026-03-31 \
  --output-path data/boe_subastas.jsonl \
  --format jsonl
```

---

### Core CLI

`boe_scraper/entrypoint.py` is the main CLI entrypoint for hitting BOE and writing results.

#### `edictos`

Command to scrape the judicial edicts section of BOE.

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
  - **`--format jsonl`**: write to a single JSONL file.

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

#### `subastas`

Command to scrape BOE auctions (`subastas.boe.es`) for real-estate auctions by province.

- **Required arguments**
  - **`--cod-provincia INT`**: INE province code.
  - **`--output-path PATH`**: where to write data.

- **Optional filters**
  - **`--from-start-date YYYY-MM-DD`**: lower bound for auction start date.
  - **`--to-start-date YYYY-MM-DD`**: upper bound for auction start date.

- **Output format**
  - **`--format csv`**: write CSV output.
  - **`--format jsonl`**: write JSONL output.

- **Logging**
  - **`--log-file FILE`**: overrides `LOG_FILE`.
  - **`--log-level LEVEL`**: overrides `LOG_LEVEL` (e.g. `INFO`, `DEBUG`).


### Python API

The same date-generation and runner logic can be used programmatically.

- **From `boe_scraper/runner/edictos.py`**
  - **`scrape_current_month(output_path: str, pattern: str, parse_only: bool = False)`**
  - **`scrape_last_week(output_path: str, pattern: str, parse_only: bool = False)`**
  - **`scrape_previous_week(output_path: str, pattern: str, parse_only: bool = False)`**
  - **`scrape_specific_month(year: int, month: int, output_path: str, pattern: str, parse_only: bool = False)`**
  - **`scrape_date_range(start_date: str, end_date: str, output_path: str, pattern: str, parse_only: bool = False)`**

- **Example**

```python
from boe_scraper.runner.edictos import scrape_date_range

results = scrape_date_range(
    start_date="2025-06-01",
    end_date="2025-06-10",
    output_path="data/boe_edictos.csv",
    parse_only=False,
    pattern=r"(JUZGADO DE LO SOCIAL.*)",
)

print(results["successful_parses"], "dates parsed successfully")
```

- **From `boe_scraper/runner/subastas.py`**
  - **`run_subastas_scraper_for_dates(cod_provincia: str, output_path: str, from_start_date: str | None = None, to_start_date: str | None = None, format: str = "jsonl")`**

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
  - Logging verbosity for all runners.

CLI options (`--download-path`, `--log-file`, `--log-level`) override these defaults for the current run only.

