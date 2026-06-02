import io
from contextlib import redirect_stdout
from unittest import IsolatedAsyncioTestCase

from jobscraper.models import JobSearchRequest, ProviderFetchError
from jobscraper.providers.jobspy_provider import JobSpyProvider
from jobscraper.settings import ScraperSettings


def request() -> JobSearchRequest:
    return JobSearchRequest(
        role="java",
        search_name="java_test",
        search_term="java",
        provider="indeed",
        location="USA",
        results_wanted=10,
        hours_old=24,
        country_indeed="USA",
    )


class FlakyJobSpyProvider(JobSpyProvider):
    def __init__(self, failures_before_success: int, settings: ScraperSettings):
        self.fetch_retries = settings.provider_fetch_retries
        self.retry_backoff_seconds = settings.provider_retry_backoff_seconds
        self.failures_before_success = failures_before_success
        self.calls = 0

    def _fetch_sync(self, request: JobSearchRequest):
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise TimeoutError("read timed out")
        return [{"title": "Java Engineer", "job_url_direct": "https://example.com/1"}]


class JobSpyProviderRetryTests(IsolatedAsyncioTestCase):
    async def test_fetch_retries_transient_timeout_then_returns_rows(self):
        provider = FlakyJobSpyProvider(
            failures_before_success=1,
            settings=ScraperSettings(
                provider_fetch_retries=2,
                provider_retry_backoff_seconds=0,
            ),
        )

        with redirect_stdout(io.StringIO()):
            rows = await provider.fetch(request())

        self.assertEqual(provider.calls, 2)
        self.assertEqual(rows[0]["title"], "Java Engineer")

    async def test_fetch_raises_provider_fetch_error_after_retry_exhaustion(self):
        provider = FlakyJobSpyProvider(
            failures_before_success=3,
            settings=ScraperSettings(
                provider_fetch_retries=1,
                provider_retry_backoff_seconds=0,
            ),
        )

        with self.assertRaises(ProviderFetchError) as context:
            with redirect_stdout(io.StringIO()):
                await provider.fetch(request())

        self.assertEqual(provider.calls, 2)
        self.assertEqual(context.exception.attempts, 2)
