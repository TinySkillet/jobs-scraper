import csv
import os
import re
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from jobspy import scrape_jobs

SITE_NAME = ["indeed"]
LOCATION = "USA"
HOURS_OLD = int(os.getenv("HOURS_OLD", "24"))
COUNTRY_INDEED = "USA"
RESULTS_WANTED = int(os.getenv("RESULTS_WANTED", "1000"))
FINAL_DIR = Path("final")
TEMP_DIR = Path("temp")

ROLE_SEARCHES = {
    "java": {
        "final_output": FINAL_DIR / "jobs_final_java.csv",
        "searches": [
            (
                "java_engineer",
                '("java developer" OR "java engineer" OR "java software engineer" OR "backend java") (spring OR "spring boot" OR microservices) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "java_developer",
                '("java developer" OR "java application developer") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "java_software_engineer",
                '("java software engineer" OR "software engineer java") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "spring_backend",
                '("spring boot developer" OR "spring developer" OR "java backend developer" OR "backend java developer") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "java_microservices",
                '(java OR "spring boot") (microservices OR "rest api" OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "backend_java",
                '("backend developer" OR "backend engineer" OR "software engineer") (java OR spring OR "spring boot") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "java_api",
                '(java OR "spring boot") (api OR kafka OR aws OR kubernetes) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "junior_java",
                '(java OR spring OR "spring boot") (junior OR associate OR "entry level" OR "early career" OR "new grad" OR "software engineer I" OR "developer I") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "mid_level_java",
                '(java OR spring OR "spring boot") ("mid level" OR "mid-level" OR intermediate OR "software engineer II" OR "developer II" OR "java developer II") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "java_rest_api",
                '("java developer" OR "java software engineer" OR "backend engineer") ("REST API" OR "RESTful API" OR "web services" OR "microservices") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "java_cloud",
                '("java developer" OR "java software engineer" OR "backend java developer") (AWS OR Azure OR GCP OR cloud OR Kubernetes OR Docker) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "enterprise_java",
                '("java developer" OR "software developer") (J2EE OR Jakarta OR Hibernate OR Maven OR Gradle OR Tomcat) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "jvm_backend",
                '("backend engineer" OR "backend developer" OR "software engineer") (JVM OR Java OR Kotlin) (Spring OR "Spring Boot" OR microservices OR API) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "java_fintech_enterprise",
                '(java OR "spring boot") (fintech OR banking OR payments OR enterprise OR "distributed systems") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
        ],
    },
    "fullstack": {
        "final_output": FINAL_DIR / "jobs_final_fullstack.csv",
        "searches": [
            (
                "fullstack_engineer",
                '("full stack developer" OR "full stack engineer" OR "full-stack developer" OR "full-stack engineer" OR fullstack) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "fullstack_frontend",
                '("full stack" OR "full-stack" OR fullstack) (react OR angular OR javascript OR typescript OR node) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "react_node",
                '("react developer" OR "react engineer") (node OR "node.js" OR express OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "typescript_node",
                '(typescript OR javascript) (node OR "node.js" OR express) ("full stack" OR fullstack OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "frontend_backend",
                '("front end" OR frontend OR react OR angular) (backend OR "back end" OR api) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "mern_stack",
                '(mern OR "mongo express react node" OR "react node") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "software_engineer_react_node",
                '("software engineer" OR developer) (react OR angular OR typescript OR javascript) (node OR "node.js" OR backend OR api) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "web_application_developer",
                '("web application developer" OR "web developer" OR "application developer") (react OR angular OR node OR "full stack" OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "javascript_fullstack",
                '(javascript OR typescript) ("full stack" OR fullstack OR backend OR api) (react OR angular OR node) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "angular_node",
                '(angular OR react) (node OR "node.js" OR api OR backend) ("software engineer" OR developer) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "junior_fullstack",
                '("full stack" OR fullstack OR react OR angular OR node OR typescript) (junior OR associate OR "entry level" OR "early career" OR "new grad" OR "software engineer I" OR "developer I") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "mid_level_fullstack",
                '("full stack" OR fullstack OR react OR angular OR node OR typescript) ("mid level" OR "mid-level" OR intermediate OR "software engineer II" OR "developer II" OR "full stack developer II") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "nextjs_fullstack",
                '("full stack" OR fullstack OR "software engineer") (Next.js OR NextJS OR React) (Node OR "node.js" OR API OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "vue_node",
                '(Vue OR Vue.js OR Nuxt OR Nuxt.js) (Node OR "node.js" OR backend OR API OR "full stack" OR fullstack) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "java_fullstack",
                '("full stack" OR fullstack OR "software engineer") (Java OR "Spring Boot") (React OR Angular OR Vue OR JavaScript OR TypeScript) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "dotnet_fullstack",
                '("full stack" OR fullstack OR "software engineer") (.NET OR "C#" OR ASP.NET) (React OR Angular OR Vue OR JavaScript OR TypeScript) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "python_fullstack",
                '("full stack" OR fullstack OR "software engineer") (Python OR Django OR Flask OR FastAPI) (React OR Angular OR Vue OR JavaScript OR TypeScript) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            (
                "frontend_api_engineer",
                '("software engineer" OR developer) (React OR Angular OR Vue OR TypeScript OR JavaScript) (REST OR GraphQL OR API OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
        ],
    },
    "data_engineer": {
        "final_output": FINAL_DIR / "jobs_final_data_engineer.csv",
        "searches": [
            (
                "data_engineer",
                '("data engineer" OR "data engineering" OR "big data engineer") (python OR sql OR spark OR airflow OR dbt OR databricks OR snowflake) -intern -internship -qa -tester -salesforce',
            ),
            (
                "etl_pipeline",
                '("etl developer" OR "etl engineer" OR "data pipeline engineer" OR "pipeline engineer") (python OR sql OR spark OR airflow OR aws OR azure OR gcp) -intern -internship -qa -tester -salesforce',
            ),
            (
                "analytics_engineer",
                '("analytics engineer" OR "data warehouse engineer" OR "data platform engineer") (sql OR dbt OR snowflake OR bigquery OR redshift OR databricks) -intern -internship -qa -tester -salesforce',
            ),
            (
                "spark_data_engineer",
                '("data engineer" OR "big data engineer") (spark OR pyspark OR databricks) -intern -internship -qa -tester -salesforce',
            ),
            (
                "snowflake_dbt",
                '("data engineer" OR "analytics engineer") (snowflake OR dbt OR "data warehouse") -intern -internship -qa -tester -salesforce',
            ),
            (
                "airflow_pipeline",
                '("data engineer" OR "pipeline engineer" OR "etl engineer") (airflow OR orchestration OR "data pipeline") -intern -internship -qa -tester -salesforce',
            ),
            (
                "python_data_engineer",
                '("data engineer" OR "etl engineer") (python OR pyspark) (sql OR spark OR airflow OR cloud) -intern -internship -qa -tester -salesforce',
            ),
            (
                "sql_data_engineer",
                '("data engineer" OR "analytics engineer") (sql OR "data warehouse") (python OR dbt OR snowflake OR bigquery) -intern -internship -qa -tester -salesforce',
            ),
            (
                "junior_data_engineer",
                '("data engineer" OR "etl developer" OR "etl engineer" OR "analytics engineer" OR "data pipeline") (junior OR associate OR "entry level" OR "early career" OR "new grad" OR "engineer I" OR "developer I") -intern -internship -qa -tester -salesforce',
            ),
            (
                "mid_level_data_engineer",
                '("data engineer" OR "etl developer" OR "etl engineer" OR "analytics engineer" OR "data pipeline") ("mid level" OR "mid-level" OR intermediate OR "engineer II" OR "developer II" OR "data engineer II") -intern -internship -qa -tester -salesforce',
            ),
            (
                "cloud_data_engineer",
                '("data engineer" OR "data platform engineer" OR "etl engineer") (AWS OR Azure OR GCP OR Glue OR "Data Factory" OR "Cloud Composer") -intern -internship -qa -tester -salesforce',
            ),
            (
                "lakehouse_engineer",
                '("data engineer" OR "data platform engineer") (lakehouse OR "data lake" OR Delta OR Iceberg OR Hive OR "Apache Hudi") -intern -internship -qa -tester -salesforce',
            ),
            (
                "streaming_data_engineer",
                '("data engineer" OR "streaming data engineer" OR "data platform engineer") (Kafka OR Flink OR streaming OR Kinesis OR Pub/Sub) -intern -internship -qa -tester -salesforce',
            ),
            (
                "data_infrastructure_engineer",
                '("data infrastructure engineer" OR "data platform engineer" OR "platform data engineer") (Python OR SQL OR Spark OR Airflow OR Kubernetes) -intern -internship -qa -tester -salesforce',
            ),
            (
                "warehouse_bi_data_engineer",
                '("data engineer" OR "analytics engineer" OR "BI engineer") (Snowflake OR BigQuery OR Redshift OR dbt OR Looker OR Tableau) -intern -internship -qa -tester -salesforce',
            ),
            (
                "azure_data_engineer",
                '("data engineer" OR "etl developer" OR "analytics engineer") (Azure OR "Azure Data Factory" OR Synapse OR Databricks OR Fabric) -intern -internship -qa -tester -salesforce',
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
EXCLUDED_TITLE_RE = re.compile(
    r"\b(lead|leader|manager|director|head|vp|vice president|chief)\b",
    re.I,
)
CLEARANCE_REQUIREMENT_RE = re.compile(
    r"\bactive\b.{0,80}\b(?:security\s+)?clearance\b|"
    r"\b(?:security\s+)?clearance\b.{0,80}\bactive\b|"
    r"\bclearance\s+required\b|"
    r"\brequires?\b.{0,80}\b(?:security\s+)?clearance\b|"
    r"\b(?:security\s+)?clearance\b.{0,80}\brequired\b|"
    r"\btop\s+secret\b|"
    r"\bts/sci\b|"
    r"\bsecret\s+clearance\b|"
    r"\bactive\b.{0,80}\b(?:secret|top secret|ts/sci|sci)\b",
    re.I | re.S,
)
JAVA_TITLE_RELEVANCE_RE = re.compile(r"\bjava\b|\bspring\b", re.I)
JAVA_BODY_RELEVANCE_RE = re.compile(
    r"\bjava\b|\bspring\b|\bspring\s+boot\b|\bj2ee\b|\bjvm\b", re.I
)
FULLSTACK_TITLE_RELEVANCE_RE = re.compile(r"\bfull[\s-]?stack\b|\bfullstack\b", re.I)
FULLSTACK_BODY_RELEVANCE_RE = re.compile(
    r"\bfull[\s-]?stack\b|\bfullstack\b|\bfrontend\b|\bfront-end\b|\bbackend\b|\bback-end\b",
    re.I,
)
DATA_ENGINEER_TITLE_RELEVANCE_RE = re.compile(
    r"\bdata engineer(?:ing)?\b|\bbig data engineer\b|\betl (?:developer|engineer)\b|\banalytics engineer\b|\bBI engineer\b|\bdata (?:pipeline|platform|warehouse|infrastructure) engineer\b|\bplatform data engineer\b|\bstreaming data engineer\b",
    re.I,
)
DATA_ENGINEER_BODY_RELEVANCE_RE = re.compile(
    r"\bdata pipeline\b|\betl\b|\bspark\b|\bairflow\b|\bdatabricks\b|\bsnowflake\b|\bdbt\b|\bbigquery\b|\bredshift\b|\bdata warehouse\b|\bdata lake\b|\blakehouse\b|\bdelta\b|\biceberg\b|\bhudi\b|\bkafka\b|\bflink\b|\bkinesis\b|\bdata factory\b|\bsynapse\b|\bfabric\b",
    re.I,
)
FRONTEND_RE = re.compile(
    r"\breact\b|\bangular\b|\bvue\b|\bnext\.?js\b|\bnuxt\.?js\b|\bjavascript\b|\btypescript\b",
    re.I,
)
BACKEND_RE = re.compile(
    r"\bnode\b|\bexpress\b|\bapi\b|\bbackend\b|\bback-end\b|\bjava\b|\bspring\b|\.net\b|\bc#\b|\bpython\b|\bdjango\b|\bflask\b|\bfastapi\b|\bgraphql\b",
    re.I,
)
DATA_ENGINEER_SKILL_RE = re.compile(
    r"\bsql\b|\bpython\b|\bspark\b|\bpyspark\b|\bairflow\b|\bdbt\b|\bdatabricks\b|\bsnowflake\b|\bbigquery\b|\bredshift\b|\baws\b|\bazure\b|\bgcp\b|\bglue\b|\bdata factory\b|\bsynapse\b|\bfabric\b|\bkafka\b|\bflink\b|\bkinesis\b",
    re.I,
)
GENERIC_ENGINEER_TITLE_RE = re.compile(
    r"\b(software engineer|developer|engineer)\b", re.I
)


def prefer_recent_indeed_results():
    """JobSpy defaults Indeed pagination to relevance; date sort keeps 24h runs fresh."""
    try:
        import jobspy.indeed as indeed_module
        import jobspy.indeed.constant as indeed_constant
    except ImportError:
        return

    for module in (indeed_module, indeed_constant):
        query = getattr(module, "job_search_query", "")
        if "sort: RELEVANCE" in query:
            module.job_search_query = query.replace("sort: RELEVANCE", "sort: DATE")


def raw_output_path(role, search_name):
    return TEMP_DIR / f"jobs_{role}_{search_name}.csv"


def parse_date_posted(value):
    value = (value or "").strip()
    if not value:
        return None

    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def posted_within_hours(row, hours_old=HOURS_OLD, today=None):
    posted_date = parse_date_posted(row.get("date_posted"))
    if not posted_date:
        return False

    # JobSpy's Indeed output only keeps the posting date, not the posting time.
    # Keep today's and yesterday's rows for a 24h run; the scrape API still gets
    # the exact hours_old filter, and this removes clearly stale leakage.
    today = today or date.today()
    allowed_calendar_days = max(1, (hours_old + 23) // 24)
    cutoff = today - timedelta(days=allowed_calendar_days)
    return posted_date >= cutoff


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

    if role == "data_engineer":
        if DATA_ENGINEER_TITLE_RELEVANCE_RE.search(title):
            return True

        return (
            GENERIC_ENGINEER_TITLE_RE.search(title)
            and DATA_ENGINEER_BODY_RELEVANCE_RE.search(description)
            and DATA_ENGINEER_SKILL_RE.search(description)
        )

    raise ValueError(f"Unknown role: {role}")


def exclusion_reason(row):
    title = row.get("title") or ""
    description = row.get("description") or ""

    if EXCLUDED_TITLE_RE.search(title):
        return "excluded_title_leadership"

    if CLEARANCE_REQUIREMENT_RE.search(f"{title}\n{description}"):
        return "requires_clearance"

    return None


def scrape_role(role, config):
    TEMP_DIR.mkdir(exist_ok=True)

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


def scrape_searches():
    prefer_recent_indeed_results()
    for role, config in ROLE_SEARCHES.items():
        scrape_role(role, config)


def build_final_csv(role, config):
    rows = []
    reasons_by_file = {}
    FINAL_DIR.mkdir(exist_ok=True)

    for search_name, _ in config["searches"]:
        path = raw_output_path(role, search_name)
        reasons = Counter()
        if not path.exists():
            reasons["missing_file"] += 1
            reasons_by_file[path.name] = reasons
            continue

        with path.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if not parse_date_posted(row.get("date_posted")):
                    reasons["missing_or_invalid_date_posted"] += 1
                    continue

                if not posted_within_hours(row):
                    reasons["older_than_hours_old"] += 1
                    continue

                direct_url = (row.get("job_url_direct") or "").strip()
                if not direct_url:
                    reasons["missing_direct_url"] += 1
                    continue

                job_type = (row.get("job_type") or "").strip().lower()
                if job_type not in ALLOWED_JOB_TYPES:
                    reasons["excluded_job_type"] += 1
                    continue

                reason = exclusion_reason(row)
                if reason:
                    reasons[reason] += 1
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
