# Running the software

## Safe local checks

Use Python 3.10+ and run from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q utils evaluate generate_data train _scripts_mcts _scripts_sos
```

These standard-library checks make no network requests, download no models, write no datasets and perform no training. Temporary test files are removed automatically. They validate isolated verifier/search/accounting behavior, not GPU training quality or reported benchmark results.

## Before using the model-backed paths

The retained dependencies and scripts target Linux with NVIDIA CUDA. The 2025 requirements pin PyTorch, vLLM, Transformers and TRL; GPU/runtime compatibility has not been requalified by the CPU maintenance checks. Install in an isolated environment on a suitable machine, not into an existing production environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt` is the retained historical dependency specification, not a complete cross-platform lockfile. Runtime modules also import HTTP/YAML tooling supplied by that dependency stack; a qualified environment should record their resolved versions. Check CUDA/PyTorch/vLLM compatibility before installation. Downloading weights and running inference/training consume storage and compute.

### Required inputs

1. **Question files.** The launchers expect `questions/train_N.txt`, `questions/dev.txt` or `questions/test.txt`, one `Use ... to make ...` question per line. Those historical files are not included.
2. **Training datasets.** The trainers expect Hugging Face datasets saved on disk, using the [documented schemas](ARCHITECTURE.md#one-search-tree-three-training-products), under configured `data/` paths. Those directories are not included.
3. **Compatible checkpoints.** Review model names, immutable revisions and tokenizers. The historical scripts contain the author's Hub namespaces and configuration-specific naming conventions; a model name is not a substitute for a qualified checkpoint/data manifest.
4. **Output destinations.** Choose new output directories and Hub repositories. Existing data exporters append loaded records and replace the target dataset directory while saving. Do not point them at an irreplaceable dataset.
5. **Authorized access.** Some Hub artifacts may require credentials or different permissions. Use normal credential tooling; never commit access tokens.

The repository retains a synthetic-data generator (`python -m utils.gen_init_data`). It enumerates a large arithmetic space, filters to positive-integer intermediate calculations and writes question/data directories. It is **not** a quickstart or a provenance-equivalent reconstruction of all historical splits. Review the generator and its output paths before running it. Its own internally generated arithmetic templates remain historical code; the corrected shared verifier is used for model-produced final answers.

## Entry points

Use module invocations from the repository root so imports resolve consistently. The commands below identify launchers and flags; they are not a one-command replay of the study.

| Operation | Module | Key flags/configuration |
| --- | --- | --- |
| Policy service | `_scripts_mcts.deploy_policy` | `--iter`, `--gpu`, `--port`; model prefix is in the launcher. |
| Value service | `_scripts_mcts.deploy_value` | `--iter`, `--gpu`, `--port`; use compatible policy/value checkpoints. |
| MCTS collection | `_scripts_mcts.generate_data` | `--iter`, `--gpu`, `--port`, `--b`, `--e`; `generate_data/config_mcts_generator.yaml`. |
| MCTS evaluation | `_scripts_mcts.evaluate` | `--iter`, `--gpu`, `--port`, `--be`, `--mode`; `evaluate/config_mcts_evaluator.yaml`. |
| Policy training | `_scripts_mcts.train_policy` | `--iter`, `--gpu`; `train/config_policy.yaml` plus launcher overrides. |
| Value training | `_scripts_mcts.train_value` | `--iter`, `--gpu`; `train/config_value.yaml` plus launcher overrides. |
| SoS service | `_scripts_sos.deploy_sos` | `--iter`, `--gpu`, `--port`, `--b`, `--e`, `--epochs`, `--tokens`. |
| SoS collection/evaluation | `_scripts_sos.sos` | `--iter`, `--gpu`, `--port`, `--mode`, optional `--b`, `--e`, `--attemps` (historical spelling). |
| SoS training | `_scripts_sos.train_sos` | Inspect its parser and `train/config_sos.yaml`; its naming convention includes branch/expansion/epoch settings. |

For example, inspect the lightweight SoS CLI without contacting a model:

```bash
python3 -m _scripts_sos.sos --help
```

Once dependencies are installed, inspect the other parsers with `python -m MODULE --help`. Some deployment modules import vLLM before parsing arguments, so even `--help` for those modules requires their runtime dependencies. The `_scripts_*` modules are the retained launchers; the older `utils/deployer_*.py` standalone `__main__` blocks are not qualified alternate launchers.

### Local port contract

The MCTS launchers compute:

```text
policy port = 8050 + 4 × gpu + 2 × port
value port  = policy port + 1
```

The SoS launchers use `8050 + 4 × gpu + port`. These are historical experiment indexing conventions, **not** automatic port allocation. Avoid collisions, choose matching service/client settings and keep services bound to localhost unless you add appropriate authentication and network controls. The HTTP services do not implement a public multi-user authorization layer.

### Collection and training sequence

1. Supply required questions and initial policy/value data or checkpoints.
2. Start matching policy and value services in separate terminals.
3. Run MCTS collection to produce policy, value and SoS datasets.
4. Train selected products, deliberately choosing the next iteration and output destinations.
5. Start the resulting services and evaluate against a frozen question set.
6. Retain checkpoint hashes, data/split hashes, exact commands/configuration, raw completions and all model-call/compute accounting for any new claim.

**Publishing side effect:** historical policy/value trainers set `push_to_hub=True`, public repositories and end-of-training uploads. The value trainer also explicitly uploads model/tokenizer artifacts. To keep a run local, disable **both** automatic and explicit publishing in the trainer code before running it. Change the author's repository names to destinations you own. This cleanup does not silently alter historical training semantics.

## What is not supplied by this cleanup

No new training runs, matched-compute benchmarks or experiment results were produced. The full historical artifact bundle has not been reconstructed or GPU-tested. Dataset access, tokenizer conventions, checkpoint compatibility, service startup and a complete run manifest must be qualified before claiming reproduction of the report. The preserved code nevertheless exposes the implemented search, data-generation, training and evaluation mechanisms for inspection and adaptation.
