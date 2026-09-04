import unittest

from data.research_benchmark.verify_readme import (
    verify_readme_highlights,
    verify_readme_results,
    verify_readme_tables,
)


class ReadmeBenchmarkTests(unittest.TestCase):
    def test_landing_page_highlights_match_saved_benchmark_summaries(self):
        verify_readme_highlights()

    def test_landing_page_results_match_saved_benchmark_summary(self):
        verify_readme_results()

    def test_published_tables_match_saved_benchmark_artifact(self):
        verify_readme_tables()


if __name__ == "__main__":
    unittest.main()
