import csv
import re
from collections import Counter
from pathlib import Path

from jobspy import scrape_jobs

SITE_NAME = ["indeed"]
LOCATION = "USA"
HOURS_OLD = 24
COUNTRY_INDEED = "USA"
RESULTS_WANTED = 500

ROLE_SEARCHES = {
    "java": {
        "final_output": Path("jobs_final_java.csv"),
        "searches": [
            (
                "java_engineer",
                '("java developer" OR "java engineer" OR "java software engineer" OR "backend java") (spring OR "spring boot" OR microservices) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "spring_backend",
                '("spring boot developer" OR "spring developer" OR "java backend developer" OR "backend java developer") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
        ],
    },
    "fullstack": {
        "final_output": Path("jobs_final_fullstack.csv"),
        "searches": [
            (
                "fullstack_engineer",
                '("full stack developer" OR "full stack engineer" OR "full-stack developer" OR "full-stack engineer" OR fullstack) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "fullstack_frontend",
                '("full stack" OR "full-stack" OR fullstack) (react OR angular OR javascript OR typescript OR node) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
        ],
    },
}

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

ALLOWED_JOB_TYPES = {"fulltime", "contract", ""}
JAVA_TITLE_RELEVANCE_RE = re.compile(r"\bjava\b|\bspring\b", re.I)
JAVA_BODY_RELEVANCE_RE = re.compile(
    r"\bjava\b|\bspring\b|\bspring\s+boot\b|\bj2ee\b|\bjvm\b", re.I
)
FULLSTACK_TITLE_RELEVANCE_RE = re.compile(r"\bfull[\s-]?stack\b|\bfullstack\b", re.I)
FULLSTACK_BODY_RELEVANCE_RE = re.compile(
    r"\bfull[\s-]?stack\b|\bfullstack\b|\bfrontend\b|\bfront-end\b|\bbackend\b|\bback-end\b",
    re.I,
)
FRONTEND_RE = re.compile(r"\breact\b|\bangular\b|\bjavascript\b|\btypescript\b", re.I)
BACKEND_RE = re.compile(
    r"\bnode\b|\bexpress\b|\bapi\b|\bbackend\b|\bback-end\b|\bjava\b|\bspring\b|\.net\b|\bc#\b|\bpython\b|\bdjango\b|\bflask\b",
    re.I,
)
GENERIC_ENGINEER_TITLE_RE = re.compile(
    r"\b(software engineer|developer|engineer)\b", re.I
)


def raw_output_path(role, search_name):
    return Path(f"jobs_{role}_{search_name}.csv")


def is_relevant(row, role):
    title = row.get("title") or ""
    description = row.get("description") or ""

    if role == "java":
        if JAVA_TITLE_RELEVANCE_RE.search(title):
            return True

        return (
            GENERIC_ENGINEER_TITLE_RE.search(title)
            and JAVA_BODY_RELEVANCE_RE.search(description)
        )

    if role == "fullstack":
        if FULLSTACK_TITLE_RELEVANCE_RE.search(title):
            return True

        return (
            GENERIC_ENGINEER_TITLE_RE.search(title)
            and FULLSTACK_BODY_RELEVANCE_RE.search(description)
            and FRONTEND_RE.search(description)
            and BACKEND_RE.search(description)
        )

    raise ValueError(f"Unknown role: {role}")


def scrape_searches():
    for role, config in ROLE_SEARCHES.items():
        for search_name, search_term in config["searches"]:
            output = raw_output_path(role, search_name)
            print(f"\n=== Running {role}: {search_name} ===")
            print(search_term)

            jobs = scrape_jobs(
                site_name=SITE_NAME,
                search_term=search_term,
                location=LOCATION,
                verbose=1,
                results_wanted=RESULTS_WANTED,
                hours_old=HOURS_OLD,
                country_indeed=COUNTRY_INDEED,
            )

            print(f"Found {len(jobs)} jobs for {role}: {search_name}")
            if jobs.empty:
                output.unlink(missing_ok=True)
                continue

            jobs.to_csv(output, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
            print(f"Saved {output}")


def build_final_csv(role, config):
    rows = []
    reasons_by_file = {}

    for search_name, _ in config["searches"]:
        path = raw_output_path(role, search_name)
        reasons = Counter()
        if not path.exists():
            reasons["missing_file"] += 1
            reasons_by_file[path.name] = reasons
            continue

        with path.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                direct_url = (row.get("job_url_direct") or "").strip()
                if not direct_url:
                    reasons["missing_direct_url"] += 1
                    continue

                job_type = (row.get("job_type") or "").strip().lower()
                if job_type not in ALLOWED_JOB_TYPES:
                    reasons["excluded_job_type"] += 1
                    continue

                if not is_relevant(row, role):
                    reasons["not_relevant"] += 1
                    continue

                rows.append(
                    {
                        column: (row.get(column) or "").strip()
                        for column in FINAL_SOURCE_COLUMNS
                    }
                )
                reasons["kept_before_dedupe"] += 1

        reasons_by_file[path.name] = reasons

    by_url = {}
    for row in rows:
        key = row["job_url_direct"].casefold()
        if key not in by_url:
            by_url[key] = row
            continue

        existing = by_url[key]
        for column in FINAL_SOURCE_COLUMNS:
            if not existing.get(column) and row.get(column):
                existing[column] = row[column]

    final_rows = list(by_url.values())
    final_rows.sort(
        key=lambda row: (
            row.get("date_posted") or "",
            row.get("company") or "",
            row.get("title") or "",
            row.get("location") or "",
        ),
        reverse=True,
    )

    final_output = config["final_output"]
    with final_output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FINAL_OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(
            {
                output_column: row[source_column]
                for source_column, output_column in FINAL_COLUMNS
            }
            for row in final_rows
        )

    print(f"\n=== Final CSV: {role} ===")
    print(f"candidate_rows_before_dedupe={len(rows)}")
    print(f"final_rows={len(final_rows)}")
    print(f"exact_direct_url_duplicates_removed={len(rows) - len(final_rows)}")
    print(f"output={final_output}")
    for file_name, reasons in reasons_by_file.items():
        print(f"\n{file_name}")
        for key, value in reasons.items():
            print(f"{key}={value}")


if __name__ == "__main__":
    scrape_searches()
    for role, config in ROLE_SEARCHES.items():
        build_final_csv(role, config)
