# Architecture and data contracts

## External neural-guided search

[`utils/mcts_base.py`](../utils/mcts_base.py) contains the node, tree, forest and run abstractions. A node holds its accumulated text state, parent/children, visit count, backed-up action value Q, initial learned value estimate V and terminal-return labels. A terminal state contains the final-answer marker.

`MCTSTree.select_child` uses the existing Q-plus-exploration rule:

```text
Q(child) + c_explore × sqrt(N(parent)) / (N(child) + 1)
```

This is a visit-dependent exploration term; it is not the usual logarithmic UCB1 expression. The final `favourite_child` uses **maximum backed-up Q**, not maximum visits. Maintenance documents the executed rule rather than silently changing the algorithm.

`MCTSForest` maintains `2 × batch_size` tree slots, a shared request queue and batched policy/value processing. This is the implemented concurrency arrangement, not a measured scaling or throughput claim. The current policy/value client performs synchronous HTTP requests; overlapping tree traversal does not imply unlimited simultaneous inference requests.

[`utils/policy_value.py`](../utils/policy_value.py) sends `(question, partial_state)` pairs to `/policy-prediction`, requests candidate next steps, then sends all proposed child states to `/value-prediction`. [`utils/deployer_policy.py`](../utils/deployer_policy.py) and [`utils/deployer_value.py`](../utils/deployer_value.py) serve those functions with vLLM/FastAPI.

During **generation**, `MCTSTree_Generate` backs up verified terminal outcomes. During **evaluation**, `MCTSTree_Evaluate` uses the learned terminal value during search and verifies only the selected final expression afterward. The exact answer checker is not an oracle guiding terminal selection in this evaluation path.

## One search tree, three training products

[`generate_data/mcts_generator.py`](../generate_data/mcts_generator.py) produces:

| Product | On-disk example schema | How it is formed |
| --- | --- | --- |
| Policy | `{"prompt": str, "completion": str}` | Each accepted terminal trajectory supplies a successful continuation. |
| Value | `{"text": str, "labels": list[float]}` | A terminal path supplies return targets for its states; nodes with backed-up terminal labels use their mean. |
| SoS | `{"prompt": str, "completion": str}` | The visited-node traversal is serialized with node/ancestor identifiers, thought markers and a chosen accepted final answer. |

These are Hugging Face `Dataset.save_to_disk` directories, not JSON files. The table shows the logical record schemas. The forest samples up to five policy and five value examples per problem and retains the serialized SoS example when available.

### Policy and contextual training

[`train/policy_trainer.py`](../train/policy_trainer.py) uses causal-LM SFT for both policy and SoS records. The `_scripts_mcts` and `_scripts_sos` launchers choose iteration-specific dataset/model identifiers and hyperparameters. The contextual generator can also retain verified successful samples for rejection/self-training.

### Step-value training

[`train/value_trainer.py`](../train/value_trainer.py) chooses a vocabulary logit for the token `1`. It aligns labels with tokenizer positions that decode to newlines, checks alignment, masks all other positions with a sentinel, and optimizes binary cross-entropy on the selected positions. Padding labels do not enter the objective. The value service takes the sigmoid of the corresponding logit at the end of a partial state.

This is a custom state-value interface built on a causal language model. It is not an ordinary final-response classification head. Tokenizer/newline compatibility is therefore part of a checkpoint's operational contract.

## Contextual search representation

The serialized traversal includes identifiers such as `N4->N2 | ...`, making branch relationships explicit in text. A selected successful expression follows `<START_ANSWER>`. [`_scripts_sos/sos.py`](../_scripts_sos/sos.py) evaluates such completions or collects successful completions on unresolved questions for later training.

The current serving launcher stops generation at `<END_ANSWER>`; vLLM may omit the stop string from returned text. The answer checker therefore requires a start marker but accepts either an explicit end marker or the end of the completion. It does not accept an unmarked equation found elsewhere in the trace.

## Exact answer verification

[`utils/arithmetic.py`](../utils/arithmetic.py) is shared by MCTS and SoS. Its contract is:

- Question: `Use n1, n2, ... to make target.`, optionally prefixed by `Q |`.
- Operands: supplied non-negative decimal integer literals, used exactly once each, counting duplicates.
- Expression: integer literals, parentheses and **binary** `+`, `-`, `*`, `/` only.
- Intermediate results may be negative or fractional; this checker does not impose the initial-data generator's positive-integer-intermediate restriction.
- The final expression must equal the integer target exactly. The written right-hand side must also be that target.
- Reordering is allowed. Concatenation, unary negation, exponentiation, floor division, modulo, function calls and arbitrary Python are rejected.
- The whole answer segment must parse, apart from optional surrounding whitespace and a final period.
- MCTS requires exactly one `The answer is:` line. SoS requires exactly one `<START_ANSWER>` marker.

The checker uses a restricted Python syntax tree as a parser, a fixed operator allowlist and `fractions.Fraction` for evaluation; it does not call `eval`. Length, operand-count, nesting and literal-size bounds reject pathological inputs. This verifies the **final expression**, not every intermediate natural-language step in a search trace.

## Evaluation records

The MCTS runner returns one selected-answer outcome per completed question and expansion budget. Current YAML exports contain:

```yaml
accuracy_by_expansions:
  25: 0.5
results_by_expansions:
  25:
    correct: 1
    completed: 2
    requested: 3
    uncompleted: 1
```

This is a **schema illustration, not an experimental result**. Accuracy is conditional on completed outcomes; the requested/completed/uncompleted counts expose incomplete execution. A budget with no completed outcomes has `null` accuracy, not a fabricated zero. Historical logs with a single placeholder `accuracy: 0.0` must not be interpreted as measured results.

The SoS token-threshold plot counts the fraction of completions that are both correct and no longer than a threshold. It is a cumulative completion statistic, not a controlled experiment that reruns a fixed model at each token budget. It is necessarily nondecreasing for fixed completions.
