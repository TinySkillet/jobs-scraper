# Job Scraper

This project scrapes recent software jobs for Java, full-stack, and data
engineering searches, then writes cleaned CSV files for each role. The current
production provider is JobSpy over Indeed. The codebase is now structured so
additional providers, such as `joeyism/linkedin_scraper`, can be added behind
the same pipeline.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) for dependency and virtual environment
  management

## Setup

Install `uv` if it is not already installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install the project dependencies:

```bash
uv sync
```

This creates a local `.venv` and installs `python-jobspy` from `uv.lock`.

To install the optional LinkedIn provider dependencies:

```bash
uv sync --extra linkedin
uv run playwright install chromium
```

## Run

Run the scraper from the repo root:

```bash
uv run python main.py
```

Or use the package entry point:

```bash
uv run job-scraper
```

The pipeline searches Indeed for every configured role, saves raw results under
`temp/`, filters and deduplicates the rows, then writes final CSVs under
`final/`. It excludes leadership and management titles such as lead, leader,
manager, director, head, VP, vice president, and chief.

Final outputs:

- `final/jobs_final_java.csv`
- `final/jobs_final_fullstack.csv`
- `final/jobs_final_data_engineer.csv`

## Local Postgres

Start a local Postgres container using the Alpine image:

```bash
docker compose up -d postgres
```

Default connection settings:

```text
DATABASE_URL=postgresql+asyncpg://jobscraper:jobscraper@localhost:5432/jobscraper
```

Override `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, or
`POSTGRES_PORT` in a local `.env` file if needed. The database data is stored in
the named Docker volume `job-scraper_postgres_data`.

Apply database migrations:

```bash
DATABASE_URL=postgresql+asyncpg://jobscraper:jobscraper@127.0.0.1:5432/jobscraper uv run alembic upgrade head
```

The scraper persists each search run, identifiable raw provider payload, and
normalized job with SQLAlchemy's async engine and `asyncpg`. CSV files are still
written as compatibility exports. Normalized jobs dedupe per provider/source key
and are soft-expired when their parsed posting time is older than the configured
job age window.

## Architecture

- `jobscraper.roles`: search catalog for each role.
- `jobscraper.providers`: source adapters. `JobSpyProvider` is active by
  default; `LinkedInScraperProvider` is present but requires LinkedIn session
  setup before it should be enabled.
- `jobscraper.pipeline`: orchestration for raw fetches, filtering, dedupe, and
  final CSV generation.
- `jobscraper.filters`: date, title, job type, clearance, and role relevance
  rules.
- `jobscraper.storage`: CSV read/write concerns.
- `jobscraper.settings`: environment-backed runtime configuration.

## Configuration

These environment variables can be used when running the scraper:

```bash
HOURS_OLD=48 RESULTS_WANTED=500 uv run python main.py
```

- `HOURS_OLD`: how far back to search, in hours. Default: `24`.
- `MAX_JOB_AGE_HOURS`: how long a parsed job posting remains active. Default:
  `72`.
- `RESULTS_WANTED`: max results to request for each search. Default: `1000`.
- `LOCATION`: location passed to providers. Default: `USA`.
- `COUNTRY_INDEED`: Indeed country passed to JobSpy. Default: `USA`.
- `JOB_PROVIDERS`: comma-separated providers to run. Default: `indeed`.
- `TEMP_DIR`: raw output directory. Default: `temp`.
- `FINAL_DIR`: final output directory. Default: `final`.
- `DATABASE_URL`: SQLAlchemy async database URL. Default:
  `postgresql+asyncpg://jobscraper:jobscraper@localhost:5432/jobscraper`.
- `DATABASE_ENABLED`: set to `0`, `false`, or `no` to skip DB persistence.
- `LINKEDIN_SESSION_PATH`: required only when enabling the LinkedIn provider.
- `LINKEDIN_HEADLESS`: set to `0`, `false`, or `no` to show the browser.

## Tags and Deduplication

Rows without a stable direct URL/source identifier are dropped before storage.
For stored rows, deduplication is source-specific: the same job from Indeed and
LinkedIn remains separate, while repeated rows from the same provider/source key
update the existing record. Tags are high-precision only and are omitted when
the source data is ambiguous. Built-in tag namespaces include `source`,
`work_mode`, `experience`, and `experience_level`.

## LinkedIn provider status

`jobscraper.providers.linkedin_provider.LinkedInScraperProvider` is a lazy
adapter for `https://github.com/joeyism/linkedin_scraper.git`. It uses the v3
flow from that package: search returns LinkedIn job URLs, then each URL is
scraped for details. It is not enabled by default because LinkedIn scraping
needs a browser runtime and an authenticated session file. Before making it
production-active, decide:

- whether this scraper should use a personal LinkedIn session, a dedicated
  scraper account, or another source of authenticated cookies;
- whether raw LinkedIn jobs should be stored even when date fields are missing;
- whether final output should remain CSV-only or move to a database first.

## Tests

Run the local tests without network access:

```bash
uv run python -m unittest discover -s tests
```

## Notes

- The scraper uses JobSpy and needs network access to query Indeed.
- Generated CSVs in `temp/` and `final/` are runtime outputs and can be
  deleted before a fresh run.
