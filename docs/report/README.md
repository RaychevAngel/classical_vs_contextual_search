# Report source

**Explicit versus learned search: Neural-guided tree search and search-trace learning**

Angel Raychev, 23 October 2026

This is the **single canonical technical report** accompanying the article: Angel's retrospective on joint 2025 work with Yalcin Tur and Mihajlo Stojkovic. It integrates the methods, original historical figures and empirical account instead of requiring readers to combine a methods-only note with a second PDF. It is not a newly coauthored paper or a new experiment. The original Stanford reports retain their original authorship and identity.

- [Read the article](https://angelraychev.com/explicit-versus-learned-search/).
- [Download the PDF](https://angelraychev.com/research/explicit-learned-search/explicit-versus-learned-search.pdf).
- [TeX source](explicit-versus-learned-search.tex).
- [Primary historical implementation snapshot](https://github.com/RaychevAngel/classical_vs_contextual_search/tree/1a7fda10617d34ccd3a87c825cba71e4429de91a).

The architecture diagrams are vector figures defined in the TeX source. Historical empirical figures are included under [`figures/`](figures/). Keep that directory alongside the TeX when building. No model weights or experimental runs are needed to build the report.

## Build

From this directory, with a recent TeX Live installation:

```bash
mkdir -p output/pdf
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir=output/pdf explicit-versus-learned-search.tex
```

Packages beyond the LaTeX base used by the report: `lmodern`, `geometry`, `microtype`, `amsmath`, `amsfonts`/`amssymb`, `mathtools`, `booktabs`, `tools` (`tabularx`/`array`), `graphics`, `xcolor`, `caption`, `float`, `placeins`, `pgf` (TikZ), `enumitem`, `fancyhdr`, `lastpage`, `titlesec`, `xurl` and `hyperref`.

Historical measurements have not been rerun or rescored for this report. Worked examples and architecture diagrams are explanatory illustrations, not newly sampled trajectories or empirical results. Source links inside the report point to the historical implementation snapshot; current maintenance is documented separately in [STATUS.md](../STATUS.md).

The [historical results archive](../../results/archive/README.md) separately preserves recovered earlier summaries and every literal point from seven plotting-script versions. It includes offline inspection and unfiltered plot-recreation commands. These earlier 0.5B records are not substituted for the final CS224R 1.5B/3B study's missing raw-run mapping.

The compiled PDF is distributed from the website and a GitHub release rather than committed as a binary in ordinary source history.
