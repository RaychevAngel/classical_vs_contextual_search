"""Recover a fixed set of historical artifacts; never execute historical code.

Requires PyYAML only for this recovery step. The checked-in JSON and inspector
are usable without PyYAML, git, model services, network access, or a GPU.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ARCHIVE = Path(__file__).resolve().parent
REPO = ARCHIVE.parents[1]
SOURCES = """
95cb79d15840ded34ad2b45a5391f5b031a805cf logs/evaluation/iteration_3.yaml
23e44648a28e41b628457f77a7aad2d480ba6a58 logs/evaluation/iteration_4.yaml
6cd7fbbe0e0f6da11ddd9c0a9ca290ae49c4abc3 results/iteration_1.yaml
4bee083e068ead53370b39bafed2aeccaefa15f6 results/iteration_2.yaml
d4b41a9c783dd4f07dc4d2c9bad07368bdc96f53 results/iteration_3.yaml
ba4bc9ca64fd2779340eb523c1ce7fdcd4ebb8ce evaluate/results/evaluation_iteration_1.yaml
4275d843b5837c9c8d3840573fc0859de5aa3d08 evaluate/results/evaluation_iteration_2.yaml
b931a5ac86161c46a3d069049a5a5c37c196bb41 evaluate/results/evaluation_iteration_3.yaml
5e3fa482e0eb3c6b04302292b505ab096c7fc0e5 evaluate/results/evaluation_iteration_4.yaml
f3f7d330a1a59296a850146bdfcea99f4c717313 evaluate/results/evaluation_iteration_1.yaml
2cb9d028b7f3aaa5941d84b0ca85dfdbdccd6a85 evaluate/results/evaluation_iteration_3.yaml
3aa921b9c7ee6c7f9f56bc3db88943a13e716806 evaluate/results/evaluation_iteration_3.yaml
19c181da23a523eb8ff49e6c8f0a7ce034a5573b evaluate/results/evaluation_iteration_1.yaml
71ae84764cfbd078e2ddff37c8cd4b1e6f40d3ae evaluate/results/evaluation_iteration_2.yaml
b598af3ee365b3a74eacbe0651c2b54be3cbcf8d evaluate/results/evaluation_iteration_3.yaml
c8a9fbd57ab780a5b2a7a56d0fbf83c0ed8aacc6 evaluate/results/evaluation_iteration_4.yaml
0a42a33278f4ad28ff0e4d1a69a87e96d4cac1cf evaluate/results/evaluation_iteration_1.yaml
f1495ebf20755921907b9572777a15b0f07dcb0a evaluate/results/evaluation_iteration_2.yaml
812f695d3ede3f0cc789ad46e61b69965444ad59 evaluate/results/evaluation_iteration_3.yaml
e0497d80a13cccd8bdeb9c9df608353c137680f4 evaluate/results/evaluation_iteration_4.yaml
b33c4a72651dce711826a0d2c6e13e93a76775ed results/evaluation_iteration_1.yaml
ad64a33b415ae9d601be8ffbbcb21c864c47d305 results/evaluation_iteration_1.yaml
0986bb58ee6a8ac927dd87f65bb2769cb8928cd0 results/create_plots.py
9666d034031624338b7b91953783afe33c92b957 results/create_plots.py
d3dca3cf3966fe5cf76e34f89008abf134bfa3d4 results/create_plots.py
4457f4e1ae3cde79003e8d4752e016afff56d374 results/create_plots.py
a787d9131090e67d95589140b9e4242555b3b0ef evaluate/results/plots/generate_plots.py
f98825aaab54a3930c4e6ffd6a512ab0e5ad27a0 evaluate/results/plots/generate_plots.py
5dabdde83eed3fe76e025c38381b3f2d7498b774 evaluate/results/plots/generate_plots.py
""".strip()
REPAIR_BLOB = "3aa921b9c7ee6c7f9f56bc3db88943a13e716806"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_json(name: str, value: object) -> dict:
    data = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    (ARCHIVE / name).write_bytes(data)
    return {"file": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def parse_yaml(text: str, blob: str) -> tuple[list, list]:
    import yaml

    repairs = []
    if blob == REPAIR_BLOB:
        lines = text.splitlines(keepends=True)
        for line_number, before, after in [
            (837, "  - accuracy: 0.31643002028397565", "- accuracy: 0.31643002028397565"),
            (856, "  accuracy: 0.4989457037427517", "- accuracy: 0.4989457037427517"),
        ]:
            assert lines[line_number - 1].rstrip("\r\n") == before
            lines[line_number - 1] = after + "\n"
            repairs.append({"line": line_number, "original": before, "parsed_as": after})
        text = "".join(lines)
    result = yaml.safe_load(text)
    if isinstance(result, dict):
        result = [result]
    assert isinstance(result, list) and all(isinstance(row, dict) for row in result)
    return result, repairs


def literal_arrays(text: str) -> list[dict]:
    arrays = []
    for node in ast.parse(text).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        name = target.id
        if name not in ("data", "data_sos_mcts") and not re.fullmatch(r"(?:compressed_)?list[1-5]_?", name):
            continue
        # Parsing literal containers does not import or run the historical script.
        value = ast.literal_eval(node.value)
        if isinstance(value, dict):
            points = [
                {"branch_factor": key[0], "max_expansions": key[1], "accuracies_pct": values}
                for key, values in value.items()
            ]
            kind = "mcts_checkpoint_grid" if name == "data" else "sos_comparison_grid"
            units = "accuracy_percent"
        else:
            points = [list(point) for point in value]
            kind = "compressed_budget_summary" if name.startswith("compressed") else "branch_expansion_observations"
            units = "accuracy_fraction"
        arrays.append({"literal_name": name, "kind": kind, "units": units, "points": points})
    return arrays


def main() -> None:
    originals = ARCHIVE / "originals"
    originals.mkdir(exist_ok=True)
    manifest = {"schema_version": 1, "sources": [], "derived": [], "notes": [
        "Fixed evidence extraction from public repository history; no inference or rescoring.",
        "Earliest changing commit identifies git provenance, not necessarily experiment execution.",
        "YAML versions are cumulative snapshots, not independent repeated trials.",
        "Final CS224R figure-to-raw-run mapping is not established by these records.",
    ]}
    unique: dict[str, dict] = {}
    plots = []
    snapshot_count = 0
    for source in SOURCES.splitlines():
        blob, historical_path = source.split(" ", 1)
        data = git("cat-file", "blob", blob)
        local = "originals/" + blob + "--" + historical_path.replace("/", "__")
        (ARCHIVE / local).write_bytes(data)
        history = git("log", "--all", "--reverse", "--format=%H%x09%cI", "--find-object=" + blob).decode().splitlines()
        commit, committed_at = history[0].split("\t")
        item = {"git_blob": blob, "historical_path": historical_path, "file": local,
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                "earliest_changing_commit": commit, "committed_at": committed_at}
        text = data.decode()
        if historical_path.endswith(".yaml"):
            rows, repairs = parse_yaml(text, blob)
            item.update({"kind": "evaluation_summary_snapshot", "record_count": len(rows), "parsing_repairs": repairs})
            snapshot_count += len(rows)
            for index, row in enumerate(rows, 1):
                signature = canonical(row)
                if signature not in unique:
                    unique[signature] = {"record_id": hashlib.sha256(signature.encode()).hexdigest(), "record": row, "occurrences": []}
                unique[signature]["occurrences"].append({"git_blob": blob, "ordinal": index})
        else:
            arrays = literal_arrays(text)
            item.update({"kind": "literal_plot_source", "array_count": len(arrays)})
            plots.append({"git_blob": blob, "historical_path": historical_path, "arrays": arrays})
        manifest["sources"].append(item)
    records = sorted(unique.values(), key=lambda row: row["record_id"])
    manifest["derived"].append(write_json("evaluation-records.json", {"schema_version": 1,
        "deduplication": "exact full-record dictionary equality; no inferred trial identity",
        "snapshot_records": snapshot_count, "unique_full_records": len(records), "records": records}))
    manifest["derived"].append(write_json("plot-arrays.json", {"schema_version": 1, "source_versions": plots}))
    manifest["summary"] = {"source_files": len(manifest["sources"]),
        "evaluation_yaml_versions": sum(s["kind"] == "evaluation_summary_snapshot" for s in manifest["sources"]),
        "plotting_source_versions": len(plots), "snapshot_records": snapshot_count, "unique_full_records": len(records)}
    write_json("manifest.json", manifest)
    print(json.dumps(manifest["summary"], indent=2))


if __name__ == "__main__":
    main()
