"""Small offline regression checks for the curated historical bundle."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent


class ArchiveTests(unittest.TestCase):
    def test_exact_source_and_occurrence_verification(self):
        spec = importlib.util.spec_from_file_location("search_artifact_inspector", ROOT / "inspect_artifacts.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.verify()
        self.assertEqual(report["source_files"], 29)
        self.assertEqual(report["snapshot_records"], 473)
        self.assertEqual(report["unique_full_records"], 210)
        self.assertEqual(report["records_without_timestamp"], 2)

    def test_full_checkpoint_grid_preserves_decreases(self):
        versions = json.loads((ROOT / "plot-arrays.json").read_text())["source_versions"]
        latest = next(v for v in versions if v["git_blob"] == "0986bb58ee6a8ac927dd87f65bb2769cb8928cd0")
        grid = next(a for a in latest["arrays"] if a["literal_name"] == "data")["points"]
        self.assertEqual(len(grid), 25)
        self.assertEqual(sum(len(row["accuracies_pct"]) for row in grid), 175)
        self.assertEqual(max(max(row["accuracies_pct"]) for row in grid), 45.13)
        first = next(row for row in grid if (row["branch_factor"], row["max_expansions"]) == (1, 4))
        self.assertEqual(first["accuracies_pct"][-2:], [22.53, 22.33])
        # These lower larger-budget points must not disappear into an envelope.
        self.assertIn({"branch_factor": 55, "max_expansions": 220,
                       "accuracies_pct": [18.77, 21.57, 42.80, 43.30, 44.67, 44.53, 44.37]}, grid)

    def test_no_inferred_timestamps_or_model_pairing(self):
        records = json.loads((ROOT / "evaluation-records.json").read_text())["records"]
        self.assertEqual(sum(not row["record"].get("timestamp") for row in records), 2)
        mixed = [row for row in records if row["record"]["policy_model"].endswith("iteration_3")
                 and row["record"]["value_model"].endswith("iteration_4")]
        self.assertEqual(len(mixed), 46)
        self.assertTrue(all("0.5B" in row["record"]["policy_model"] for row in records))


if __name__ == "__main__":
    unittest.main()
