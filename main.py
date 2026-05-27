import csv

from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=[
        "indeed",
        "linkedin",
        "google",
        "glassdoor",
    ],
    search_term="data engineer",
    location="USA",
    results_wanted=300,  # 1000 is very high for a 24hr window; 300 is a safer target
    hours_old=24,  # Filters for jobs posted in the last 24 hours
    country_indeed="USA",
    linkedin_fetch_description=True,
)

print(f"Found {len(jobs)} jobs")
if not jobs.empty:
    print(jobs.head())
    # Save results
    jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
else:
    print("No jobs found matching the criteria.")
