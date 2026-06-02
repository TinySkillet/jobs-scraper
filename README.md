# Job Scraper

This branch scrapes recent Indeed jobs for Java, full-stack, and data
engineering searches, then writes cleaned CSV files for each role.

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

## Run

Run the scraper from the repo root:

```bash
uv run python main.py
```

The script searches Indeed for every configured role, saves raw results under
`temp/`, filters and deduplicates the rows, then writes final CSVs under
`final/`. It excludes leadership and management titles such as lead, leader,
manager, director, head, VP, vice president, and chief.

Final outputs:

- `final/jobs_final_java.csv`
- `final/jobs_final_fullstack.csv`
- `final/jobs_final_data_engineer.csv`

## Configuration

The defaults are set in `main.py`, but these environment variables can be used
when running the script:

```bash
HOURS_OLD=48 RESULTS_WANTED=500 uv run python main.py
```

- `HOURS_OLD`: how far back to search, in hours. Default: `24`.
- `RESULTS_WANTED`: max results to request for each search. Default: `1000`.

## Notes

- The scraper uses JobSpy and needs network access to query Indeed.
- Generated CSVs in `temp/` and `final/` are runtime outputs and can be
  deleted before a fresh run.
