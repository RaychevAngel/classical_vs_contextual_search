"""Replot saved observations, without model calls, rescoring, or curve filtering.

Requires matplotlib. Original arrays and all their source versions remain in
plot-arrays.json. Generated plots are clearly labeled historical reconstructions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LATEST_GRID = "0986bb58ee6a8ac927dd87f65bb2769cb8928cd0"
LATEST_CONTOURS = "a787d9131090e67d95589140b9e4242555b3b0ef"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Directory for derived SVG/PNG files")
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    versions = json.loads((ROOT / "plot-arrays.json").read_text())["source_versions"]
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "savefig.bbox": "tight"})
    outputs = []

    def save(fig, name: str) -> None:
        for extension in ("svg", "png"):
            path = args.output / f"{name}.{extension}"
            fig.savefig(path, dpi=180)
            outputs.append(str(path))
        plt.close(fig)

    grid_version = next(v for v in versions if v["git_blob"] == LATEST_GRID)
    for array in grid_version["arrays"]:
        points = sorted(array["points"], key=lambda p: (p["branch_factor"] * p["max_expansions"], p["branch_factor"], p["max_expansions"]))
        fig, ax = plt.subplots(figsize=(9, 5.5))
        columns = len(points[0]["accuracies_pct"])
        labels = ([f"Source checkpoint column {i + 1}" for i in range(columns)]
                  if array["kind"] == "mcts_checkpoint_grid" else ["SoS", "SoS + STaR", "Recorded MCTS comparison"])
        for column, label in enumerate(labels):
            # Every recorded point survives. Even a lower accuracy at a larger
            # budget is retained; lines merely join neighboring saved points.
            ax.plot([p["branch_factor"] * p["max_expansions"] for p in points],
                    [p["accuracies_pct"][column] for p in points], marker="o", markersize=3, label=label)
        ax.set_xscale("log")
        ax.set_xlabel("Branch factor × expansion limit (work proxy, not measured tokens)")
        ax.set_ylabel("Recorded accuracy (%)")
        ax.set_title("Historical plotting arrays — all recorded points")
        ax.legend(fontsize=8, ncol=2)
        ax.grid(alpha=.18)
        fig.text(.01, -.01, f"Source blob {LATEST_GRID[:12]}; model/run mapping incomplete; no new evaluation", fontsize=8)
        save(fig, array["literal_name"] + "-all-points")

    old_version = next(v for v in versions if v["git_blob"] == LATEST_CONTOURS)
    raw = [a for a in old_version["arrays"] if a["kind"] == "branch_expansion_observations"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    for ax, array in zip(axes.flat, raw):
        points = array["points"]
        cloud = ax.scatter([p[0] for p in points], [p[1] for p in points], c=[p[2] for p in points],
                           vmin=0, vmax=.6, cmap="viridis", s=42, edgecolors="black", linewidths=.3)
        ax.set_xlabel("Branch factor")
        ax.set_ylabel("Expansion limit")
        ax.set_title(f"Source {array['literal_name']} — {len(points)} observations")
        fig.colorbar(cloud, ax=ax, label="Recorded accuracy (fraction)")
    for ax in list(axes.flat)[len(raw):]:
        ax.set_visible(False)
    fig.suptitle("Earlier parameter-grid observations — no interpolation or point selection\n"
                 f"Source blob {LATEST_CONTOURS[:12]}; no new evaluation", fontsize=13)
    save(fig, "earlier-parameter-grids-all-points")
    print(json.dumps({"outputs": outputs, "evaluations_performed": 0}, indent=2))


if __name__ == "__main__":
    main()
