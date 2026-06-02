from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


JobRow = Mapping[str, Any]


@dataclass(frozen=True)
class SearchSpec:
    name: str
    term: str
    provider: str = "indeed"


@dataclass(frozen=True)
class RoleSearchConfig:
    role: str
    final_output_name: str
    searches: tuple[SearchSpec, ...]

    def final_output_path(self, final_dir: Path) -> Path:
        return final_dir / self.final_output_name


@dataclass(frozen=True)
class JobSearchRequest:
    role: str
    search_name: str
    search_term: str
    provider: str
    location: str
    results_wanted: int
    hours_old: int
    country_indeed: str


class JobProvider(Protocol):
    name: str

    async def fetch(self, request: JobSearchRequest) -> Sequence[JobRow]:
        """Fetch job rows for one search request."""


@dataclass(frozen=True)
class SearchRunRecord:
    id: int
    provider: str
    role: str
    search_name: str
    search_term: str

