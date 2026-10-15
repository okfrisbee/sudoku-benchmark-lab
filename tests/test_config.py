import tempfile
import unittest
from pathlib import Path

from sudoku_benchmark_lab.config import DEFAULT_CONFIG, load_config


class ConfigTests(unittest.TestCase):
    def test_defaults_are_complete_and_copied(self):
        config = load_config()
        self.assertEqual(config["generation"]["clue_percent_ranges"]["easy"], (0.75, 0.85))
        self.assertEqual(config["benchmark"]["solver_timeout_seconds"], 60.0)
        config["paths"]["datasets_dir"] = "changed"
        self.assertNotEqual(DEFAULT_CONFIG["paths"]["datasets_dir"], "changed")

    def test_nested_overrides(self):
        with tempfile.TemporaryDirectory() as root:
            config = load_config({
                "paths": {"datasets_dir": str(Path(root) / "puzzles")},
                "benchmark": {"solver_timeout_seconds": 12.5},
            })
        self.assertEqual(config["paths"]["datasets_dir"], str(Path(root) / "puzzles"))
        self.assertEqual(config["benchmark"]["solver_timeout_seconds"], 12.5)
        self.assertEqual(config["generation"]["clue_percent_ranges"]["hard"], (0.25, 0.35))

    def test_invalid_overrides_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "positive number"):
            load_config({"benchmark": {"solver_timeout_seconds": 0}})
        with self.assertRaisesRegex(ValueError, "(?i)clue percent range"):
            load_config({"generation": {"clue_percent_ranges": {"easy": (0.9, 0.7)}}})


if __name__ == "__main__":
    unittest.main()
