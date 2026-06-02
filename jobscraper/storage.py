from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping

from jobscraper.models import SearchSpec

FINAL_COLUMNS = [
    ("title", "Title"),
    ("company", "Company"),
    ("location", "Location"),
    ("is_remote", "Is Remote?"),
    ("job_type", "Job Type"),
    ("date_posted", "Date Posted"),
    ("job_url_direct", "Direct URL"),
    ("min_amount", "Min Amount"),
    ("max_amount", "Max Amount"),
]
FINAL_SOURCE_COLUMNS = [source_column for source_column, _ in FINAL_COLUMNS]
FINAL_OUTPUT_COLUMNS = [output_column for _, output_column in FINAL_COLUMNS]


class CsvJobStore:
    def __init__(self, *, temp_dir: Path, final_dir: Path) -> None:
        self.temp_dir = temp_dir
        self.final_dir = final_dir

    def raw_output_path(self, role: str, search: SearchSpec) -> Path:
        if search.provider == "indeed":
            return self.temp_dir / f"jobs_{role}_{search.name}.csv"

        return self.temp_dir / f"jobs_{search.provider}_{role}_{search.name}.csv"

    def write_raw(self, path: Path, rows: Iterable[Mapping[str, object]]) -> int:
        self.temp_dir.mkdir(exist_ok=True)
        rows = list(rows)
        if not rows:
            path.unlink(missing_ok=True)
            return 0

        fieldnames = self._fieldnames(rows)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_NONNUMERIC,
                escapechar="\\",
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(
                {key: _csv_value(row.get(key, "")) for key in fieldnames}
                for row in rows
            )

        return len(rows)

    def iter_raw_rows(self, path: Path):
        with path.open(newline="", encoding="utf-8-sig") as f:
            yield from csv.DictReader(f)

    def write_final(self, path: Path, rows: Iterable[Mapping[str, str]]) -> None:
        self.final_dir.mkdir(exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FINAL_OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(
                {
                    output_column: row[source_column]
                    for source_column, output_column in FINAL_COLUMNS
                }
                for row in rows
            )

    def _fieldnames(self, rows: list[Mapping[str, object]]) -> list[str]:
        seen: set[str] = set()
        fieldnames: list[str] = []
        for row in rows:
            for key in row:
                if key not in seen:
                    fieldnames.append(str(key))
                    seen.add(str(key))
        return fieldnames


def _csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)

