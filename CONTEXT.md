# Job Scraper Context

## Domain Vocabulary

### Search run

A single provider query for one role search. It records the provider, role,
search name, search term, raw row count, and start/finish timestamps.

### Provider row

A raw row returned by a provider adapter such as JobSpy or LinkedIn. Provider
rows can have source-specific fields and are not trusted until they pass the job
row lifecycle.

### Source row

A provider row that has a stable `source_key` and direct job URL. Source rows are
eligible for raw persistence and later normalization.

### Normalized job

A source row after date parsing, filtering, relevance checks, expiration
calculation, and tag extraction. Normalized jobs are eligible for database
upsert and final CSV export.

### Source key

A stable provider-specific identity for deduplication. It is derived from a
canonical direct job URL or a provider job id.

### Job row lifecycle

The flow that turns provider rows into source rows, normalized jobs, and filter
reasons. It owns source identity checks, freshness rules, active-retention
calculation, relevance checks, and tag extraction.

### Tag

A high-confidence label extracted from provider row fields, such as source,
work mode, experience requirement, or experience level. Tags are omitted when
the provider row is ambiguous.

### Final CSV export

The compatibility output written for each role after active normalized jobs are
deduplicated, sorted, and projected to user-facing columns.
