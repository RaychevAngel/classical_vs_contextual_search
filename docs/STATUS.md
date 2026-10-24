# Maintenance and research status

## Historical work

The repository contains the 2025 Stanford project implementation and its subsequent maintenance. The original main commit is preserved in ordinary git history:

```text
1a7fda10617d34ccd3a87c825cba71e4429de91a
```

The project progressed from the earlier CS224N policy/value/search study into the CS224R comparison with contextual search. The initial README described SmolLM2 sizes; the later report and retained launchers include Qwen-based configurations. Those stages should not be collapsed into a single model-size grid.

The [public Stanford report](https://cs224r.stanford.edu/spring_2025/projects/pdfs/CS_224R_Final_Report__3_%20%281%29.pdf) records the original experimental account and team contributions. The report remains a historical source; maintenance does not rewrite its past measurements.

## Bounded maintenance — 23 October 2026

- Replaces permissive final-expression `eval` checking in **both MCTS and SoS** with one restricted syntax-tree/Fraction verifier.
- Requires unambiguous final-answer markers and full answer-segment parsing.
- Fixes the SoS missing-marker check; the old index arithmetic could turn a missing marker into a nonnegative position.
- Documents the actual maximum-Q final-selection rule without changing it to a different algorithm.
- Saves actual per-budget MCTS accuracies and outcome denominators instead of the previous placeholder single `accuracy: 0.0` field. Missing completed outcomes remain visible.
- Makes isolated CPU checks possible without importing GPU or visualization dependencies.
- Clarifies that the SoS token-threshold plot is a cumulative completion statistic and handles an empty set of correct completions without plotting an undefined range.
- Adds CPU regression tests and continuous integration.

The corrected checker accepts fractional/negative intermediate calculations but does not independently validate each narrated intermediate step. It defines a precise final-expression contract; it does not retroactively establish what outputs historical runs produced.

## Evidence boundaries

Implemented search/training mechanisms, source history and released experimental checkpoint files are inspectable. A full original raw-results/checkpoint/data manifest is not packaged here. In particular, an initial model snapshot is not necessarily a trained checkpoint, and linked checkpoints need not form one matched experimental configuration.

Historical figure provenance and compute comparisons need fresh qualification before reusing their performance conclusions. Replacing the checker or an export field cannot rescore outputs that have not been recovered. No result, speedup or scaling law has been newly established by this maintenance.

## A possible new study—not an executed result

An interpretable continuation would compare external structured search and contextual search under specified training and inference resources. Useful contrasts include structural/depth generalization, where state is stored and reused, or how branch decisions are controlled. Choose one contrast first.

For a finite puzzle with complete legal enumeration, exhaustive search can find every existing solution. The scientific issue is efficiency and generalization under constraints, not a claim that contextual reasoning escapes finite enumeration. External neural-guided search and learned contextual search also share learned components; they are not a clean “classical versus AI” dichotomy.

Any new result should separately record discovery and final-selection correctness, exact-verifier outcomes, repeated states, invalid actions and full policy/value/context cost. A system-level comparison can be informative without isolating a mechanism, but it must not be presented as proving that one differing component caused the result.
