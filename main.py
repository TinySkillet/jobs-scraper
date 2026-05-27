import csv
import re
from collections import Counter
from pathlib import Path

from jobspy import scrape_jobs

SEARCHES = [
    (
        "fullstack_java",
        '("full stack" OR fullstack OR "full-stack") (java OR "spring boot" OR spring) -intern -internship -android -mobile -qa -tester -salesforce',
    ),
    (
        "java_engineer",
        '("java developer" OR "java engineer" OR "java software engineer" OR "backend java") (spring OR "spring boot" OR microservices) -intern -internship -android -mobile -qa -tester -salesforce',
    ),
    (
        "fullstack_frontend",
        '("full stack developer" OR "full stack engineer" OR "full-stack developer" OR "full-stack engineer") (react OR angular OR javascript OR typescript) -intern -internship -android -mobile -qa -tester -salesforce',
    ),
]

RAW_OUTPUTS = [Path(f"jobs_{name}.csv") for name, _ in SEARCHES]
FINAL_OUTPUT = Path("jobs_final.csv")

FINAL_COLUMNS = [
    "title",
    "company",
    "location",
    "is_remote",
    "job_type",
    "date_posted",
    "job_url_direct",
    "site",
    "job_url",
    "min_amount",
    "max_amount",
    "interval",
    "currency",
]

ALLOWED_JOB_TYPES = {"fulltime", "contract", ""}
TITLE_RELEVANCE_RE = re.compile(r"\bfull[\s-]?stack\b|\bjava\b|\bspring\b", re.I)
BODY_RELEVANCE_RE = re.compile(r"\bjava\b|\bspring\b|\bspring\s+boot\b|\bj2ee\b|\bjvm\b", re.I)
FRONTEND_RE = re.compile(r"\breact\b|\bangular\b|\bjavascript\b|\btypescript\b", re.I)
GENERIC_ENGINEER_TITLE_RE = re.compile(r"\b(software engineer|developer|engineer)\b", re.I)


def is_relevant(row):
    title = row.get("title") or ""
    description = row.get("description") or ""

    if TITLE_RELEVANCE_RE.search(title):
        return True

    return (
        GENERIC_ENGINEER_TITLE_RE.search(title)
        and BODY_RELEVANCE_RE.search(description)
        and FRONTEND_RE.search(description)
    )


def scrape_searches():
    for name, search_term in SEARCHES:
        output = Path(f"jobs_{name}.csv")
        print(f"\n=== Running {name} ===")
        print(search_term)

        jobs = scrape_jobs(
            site_name=["indeed"],
            search_term=search_term,
            location="USA",
            verbose=1,
            results_wanted=300,
            hours_old=24,
            country_indeed="USA",
        )

        print(f"Found {len(jobs)} jobs for {name}")
        if jobs.empty:
            continue

        jobs.to_csv(output, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
        print(f"Saved {output}")


def build_final_csv():
    rows = []
    reasons_by_file = {}

    for path in RAW_OUTPUTS:
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

                if not is_relevant(row):
                    reasons["not_relevant"] += 1
                    continue

                rows.append({column: (row.get(column) or "").strip() for column in FINAL_COLUMNS})
                reasons["kept_before_dedupe"] += 1

        reasons_by_file[path.name] = reasons

    by_url = {}
    for row in rows:
        key = row["job_url_direct"].casefold()
        if key not in by_url:
            by_url[key] = row
            continue

        existing = by_url[key]
        for column in FINAL_COLUMNS:
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

    with FINAL_OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FINAL_COLUMNS)
        writer.writeheader()
        writer.writerows(final_rows)

    print("\n=== Final CSV ===")
    print(f"candidate_rows_before_dedupe={len(rows)}")
    print(f"final_rows={len(final_rows)}")
    print(f"exact_direct_url_duplicates_removed={len(rows) - len(final_rows)}")
    print(f"output={FINAL_OUTPUT}")
    for file_name, reasons in reasons_by_file.items():
        print(f"\n{file_name}")
        for key, value in reasons.items():
            print(f"{key}={value}")


if __name__ == "__main__":
    scrape_searches()
    build_final_csv()
