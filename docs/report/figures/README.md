# Original empirical figures

These seven images are unmodified assets recovered from the original Overleaf projects on 23 October 2026. They are historical experimental figures, not newly rendered measurements or image-digitized data. The report's three architecture diagrams are vector drawings authored directly in its LaTeX source.

| Current asset | Original project | Original filename |
| --- | --- | --- |
| `cs224n-training.png` | *Size Doesn't Matter If You Search Enough* (CS224N) | `Accuracy_vs_TestCompute_135x135_1_2.png` |
| `cs224n-capacity-search.png` | Same | `Accuracy_vs_TestCompute_model_sizes.png` |
| `cs224n-search-135m.png` | Same | `Branch_Factor_vs_Num_Expansions_135x135.png` |
| `cs224n-search-360m.png` | Same | `Branch_Factor_vs_Num_Expansions_360x360.png` |
| `cs224n-search-1700m.png` | Same | `Branch_Factor_vs_Num_Expansions_1700x1700.png` |
| `cs224r-training.png` | *CS 224R Final Report*: *In-context Search: Efficiency Boost or Fundamentally New Capability?* | `mcts.png` |
| `cs224r-comparison.png` | Same | `sos_comparison.png` |

Original CS224N authors: Yalcin Tur, Mihajlo Stojkovic and Angel Raychev. Original CS224R authors: Angel Raychev, Yalcin Tur and Mihajlo Stojkovic. The consolidated retrospective is authored by Angel Raychev and preserves the original collaboration's credit.

The earlier Git plotting snapshots in `results/archive/` belong to different developmental configurations. They must not be substituted for these final-report figures. In particular, their maximum reported MCTS accuracy is not the final report's 51.13% figure, and they do not contain the same long-traversal comparison.

The original CS224N horizontal-axis label “FLOPs-seconds” and CS224R label “tokens” are retained. They are historical resource conventions, not newly measured end-to-end compute. The contours interpolate between measured red points. See the report for the interpretation of each plot and table.
