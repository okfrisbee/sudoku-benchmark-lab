import json
from pathlib import Path
import tempfile
import unittest

from sudoku_benchmark_lab.datasets.generation import generate_dataset_records
from sudoku_benchmark_lab.datasets.io import read_dataset, write_dataset_records
from tests.config_helpers import temporary_config


class DatasetTests(unittest.TestCase):
    def test_roundtrip_and_legacy_fields(self):
        records = generate_dataset_records(4, "easy", 1, seed=123)
        with tempfile.TemporaryDirectory() as root:
            with temporary_config(root, datasets_dir=root):
                path = write_dataset_records(records, 4, "easy")
                self.assertEqual(path.name, "4x4_easy_1.jsonl")
                self.assertEqual(read_dataset(path), records)
                legacy = {**records[0], "verification_mode": "derived", "unique": False}
                path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
                self.assertEqual(read_dataset(path)[0], legacy)

    def test_rejects_mismatched_metadata_and_writer_size(self):
        record = generate_dataset_records(4, "easy", 1, seed=123)[0]
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "wrong.jsonl"
            path.write_text(json.dumps({**record, "size": 9}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mismatched size"):
                read_dataset(path)
            with temporary_config(root, datasets_dir=root):
                with self.assertRaisesRegex(ValueError, "size does not match"):
                    write_dataset_records([record], 9, "easy")


if __name__ == "__main__":
    unittest.main()
