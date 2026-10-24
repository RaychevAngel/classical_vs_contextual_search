# Historical results archive

This is an inspectable evidence bundle recovered from the repository's **2025 git history**. It supports inspection and offline figure reconstruction, not a new model evaluation. Exact originals, derived machine-readable records and provenance are kept separately.

## What is here

| Evidence family | Preserved material | What it establishes |
| --- | --- | --- |
| Evaluation summaries, April–May 2025 | 22 exact YAML file versions; 473 records across cumulative snapshots; **210 distinct full-record dictionaries** | Recorded accuracies together with available policy/value IDs, branch/expansion settings, temperature, question path and timestamps. All named model IDs in these records are 0.5B models. |
| Later plotting arrays | Four exact versions of `results/create_plots.py`, with every literal array extracted to JSON | Checkpoint-column accuracy grids and one SoS comparison table. The latest source contains 25 configurations × seven columns, plus five configurations × three comparison columns. |
| Earlier parameter-grid arrays | Three exact versions of `evaluate/results/plots/generate_plots.py` | The saved branch-factor/expansion/accuracy triples and separate compressed budget summaries. The latest version contains 164 uncompressed triples and 40 compressed summaries. |

Repeated cumulative file snapshots are **not repeated independent trials**. Deduplication uses equality of the entire saved dictionary, not an inferred experimental identity. Different dictionaries can still describe related runs. Original order and every occurrence remain traceable through `(git_blob, ordinal)` references.

- [`manifest.json`](manifest.json): exact git blob IDs, original paths, earliest changing commits, byte counts and SHA-256 checksums.
- [`originals/`](originals/): exact bytes from all 29 recovered git objects. Historical plotting files are preserved **as evidence**, not recommended entry points.
- [`evaluation-records.json`](evaluation-records.json): all 210 distinct records, without silently filling missing fields or changing model identifiers.
- [`plot-arrays.json`](plot-arrays.json): **all seven source versions**, every literal point, and explicit units/array types.
- [`inspect_artifacts.py`](inspect_artifacts.py): standard-library-only verification of checksums, git blob identities, complete record-occurrence coverage and every extracted plotting literal.
- [`recreate_plots.py`](recreate_plots.py): clearly labeled figures from saved arrays, with no inference or rescoring.
- [`recover_from_git.py`](recover_from_git.py): deterministic recovery from the fixed object list. Requires this repository's history and PyYAML; inspection of the committed archive does not.

## Inspect without a GPU or network

From the repository root:

```bash
python3 -S results/archive/inspect_artifacts.py
python3 -S -m unittest discover -s results/archive -p 'test_*.py' -v
```

The inspector verifies all original/derived hashes, source blob identities, the deduplication identities and occurrence coverage, and exact equality of the archived plotting literals. It reads data; it never imports a historical plotting script or contacts a model service.

To regenerate the archive from existing local git objects, in a separate working copy with PyYAML available:

```bash
python3 results/archive/recover_from_git.py
python3 -S results/archive/inspect_artifacts.py
```

Recovery overwrites only the fixed files of this derived archive. It performs no network requests. Missing git objects cause a failure rather than substitution from another run.

## Recreate figures from saved data

With matplotlib installed in an isolated plotting environment:

```bash
python3 results/archive/recreate_plots.py --output /tmp/search-historical-plots
```

This produces SVG and PNG figures for the latest saved checkpoint grid, SoS table and earlier raw parameter grids. JSON retains all older versions as well. The recreation deliberately differs from the original plotting presentation:

- **Every recorded point remains visible.** No nondecreasing envelope removes lower points at larger budgets.
- The horizontal product `branch_factor × expansion_limit` is called a **work proxy**, not measured tokens or FLOPs. The original later script multiplied this product by 20 and labeled it “tokens”; that constant does not turn it into measured generation cost.
- Earlier parameter-grid observations are shown as points, not a cubic-interpolated accuracy surface.
- Checkpoint columns remain source checkpoint columns. The literal table alone does not resolve immutable model revisions or every training iteration.
- The SoS table's third column is called **“Recorded MCTS comparison,”** not “best MCTS.” At `(1, 4)`, its 22.33 differs from the maximum 22.53 in the saved checkpoint grid.

Replotting saved values is not a rerun of the study. No new predictions, correctness judgments, accuracy estimates or confidence intervals are generated.

## Provenance and interpretation

### These are not the final CS224R raw results

The YAML timestamps range from **28 April to 12 May 2025**, where present; two records have no timestamp. Their model IDs identify 0.5B policy/value experiments, including mixed pairings such as policy iteration 3 with value iteration 4. Filenames do not override those actual model IDs.

The recovered final CS224R report describes a **1.5B policy + 1.5B value model versus 3B contextual-search models**. Its reported 51.13% maximum and original images are not reconstructed by the later archived array, whose maximum is 45.13%. The original final figure bytes also differ from the known git plotting exports. A complete figure-to-run/raw-output join for that final study has **not** been established. The [canonical report](https://angelraychev.com/research/explicit-learned-search/explicit-versus-learned-search.pdf) keeps the historical studies distinct.

### Saved summaries are not per-question outcomes

The YAML files retain scalar accuracies and settings, not raw completions or complete per-question outcomes/denominators. The historical evaluator's stopping rule depended on `epsilon` and `delta`; those settings vary. Its implementation at [`07bf8d4`](https://github.com/RaychevAngel/classical_vs_contextual_search/blob/07bf8d4b3c02bcc45187c8e3522530a3661bea11/evaluate/mcts_evaluator.py) requested `ceil(log(2/delta)/(2*epsilon**2))` collected results. Do not invent a common sample size, reverse-engineer exact denominators from rounded accuracy, pool runs, or manufacture confidence intervals from these summaries.

### One original YAML snapshot has two syntax defects

Blob `3aa921b9c7ee6c7f9f56bc3db88943a13e716806` is preserved **unaltered** in `originals/`. The derived parser makes two explicitly recorded list/indentation repairs at original lines 837 and 856 so all 46 records can be recovered. The exact before/after text is in `manifest.json` and the recovery script. No numerical value or other field is changed. The original blob is not presented as valid YAML.

### Further artifacts remain in ordinary git history

The repository history also preserves generated training-loss/parameter-grid PNGs and `value_model_results.npz` (blob `210fb020447c25932566997b98d0001f483a61cb`, 4,921,888 bytes). The NPZ contains 125,623 predictions/labels and saved ROC/precision-recall arrays, but it lacks a complete immutable model/split manifest; it is not a qualified held-out metric for the final study. These larger artifacts are not duplicated in this compact archive. Retrieve a specific original with `git cat-file blob <object-id>` only after checking its provenance; never use pickle-loading for an untrusted NumPy archive.

Current strict arithmetic verification was added in October 2026. It has **not** been applied retroactively to these records because the original outputs needed for rescoring have not been recovered. See [maintenance status](../../docs/STATUS.md).
