"""Verify the saved artifact bundle offline, using only the standard library.

The module name intentionally does not shadow Python's standard inspect module.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text())


def verify() -> dict:
    manifest = load("manifest.json")
    for artifact in manifest["sources"] + manifest["derived"]:
        path = ROOT / artifact["file"]
        assert path.resolve().is_relative_to(ROOT), "Archive path escapes its root"
        data = path.read_bytes()
        assert len(data) == artifact["bytes"], f"Size mismatch: {path.name}"
        assert hashlib.sha256(data).hexdigest() == artifact["sha256"], f"Hash mismatch: {path.name}"
        if "git_blob" in artifact:
            digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            assert digest == artifact["git_blob"], f"Git blob mismatch: {path.name}"
    evaluations = load("evaluation-records.json")
    ids = set()
    total_occurrences = 0
    source_counts = {}
    for row in evaluations["records"]:
        canonical = json.dumps(row["record"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        assert hashlib.sha256(canonical.encode()).hexdigest() == row["record_id"]
        assert row["record_id"] not in ids
        ids.add(row["record_id"])
        for occurrence in row["occurrences"]:
            source_counts.setdefault(occurrence["git_blob"], []).append(occurrence["ordinal"])
            total_occurrences += 1
    assert len(ids) == evaluations["unique_full_records"] == manifest["summary"]["unique_full_records"]
    assert total_occurrences == evaluations["snapshot_records"] == manifest["summary"]["snapshot_records"]
    for source in manifest["sources"]:
        if source["kind"] == "evaluation_summary_snapshot":
            assert sorted(source_counts[source["git_blob"]]) == list(range(1, source["record_count"] + 1))
    # Independently reconstruct every plot literal from archived source, not
    # just its JSON checksum. No historical plotting module is executed.
    plotting = load("plot-arrays.json")
    scalar_values = 0
    for version in plotting["source_versions"]:
        source = next(s for s in manifest["sources"] if s["git_blob"] == version["git_blob"])
        nodes = ast.parse((ROOT / source["file"]).read_text()).body
        literals = {node.targets[0].id: ast.literal_eval(node.value)
                    for node in nodes if isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in {a["literal_name"] for a in version["arrays"]}}
        assert len(literals) == len(version["arrays"])
        for array in version["arrays"]:
            original = literals[array["literal_name"]]
            if isinstance(original, dict):
                recovered = {(p["branch_factor"], p["max_expansions"]): p["accuracies_pct"] for p in array["points"]}
                scalar_values += sum(len(values) for values in recovered.values())
            else:
                recovered = [tuple(point) for point in array["points"]]
                scalar_values += len(recovered)
            assert recovered == original, f"Incomplete literal recovery: {version['git_blob']} {array['literal_name']}"
    timestamps = sorted(row["record"]["timestamp"] for row in evaluations["records"] if row["record"].get("timestamp"))
    return {**manifest["summary"], "timestamp_range_where_recorded": [timestamps[0], timestamps[-1]],
            "records_without_timestamp": sum(not r["record"].get("timestamp") for r in evaluations["records"]),
            "plot_values_or_tuples_across_source_versions": scalar_values,
            "verification": "all hashes, blob identities, record occurrences and plotting literals match"}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
