# mini-lab

mini-lab is a research layer on top of [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent).
It adds software engineering practices (Requirements, Planning, Testing, Review) as optional modules and measures
how each changes the agent's patches, cost and behaviour. Experiments run on
[SWE-bench-Live](https://github.com/microsoft/SWE-bench-Live) (lite split).

mini-SWE-agent itself stays unchanged in `src/minisweagent/` and is the baseline: with all modules off,
mini-lab must behave exactly like it. Everything specific to this fork lives in this `minilab/` folder.

## Starting point

| | |
|---|---|
| Upstream | [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) |
| Forked at | `04d809c` (v2.4.6 + 3 commits, 2026-09-03) |
| Reference branch | `upstream-base` (never changes; `git diff upstream-base main` shows all changes of this fork) |

To pull later upstream changes:

```bash
git remote add upstream https://github.com/SWE-agent/mini-swe-agent.git
git fetch upstream && git merge upstream/main
```

## Layout

```
minilab/
├── README.md                 this file
├── core/
│   ├── context.py            shared context of one attempt: task, artifacts with provenance, events, costs, tokens
│   ├── module.py             Module base class (the hooks), module loading, prompt sections (Add / Replace)
│   ├── agent.py              LabAgent: mini's DefaultAgent + hooks; no modules = plain mini
│   ├── helper_llm.py         ask(): extra LLM calls by modules, cost and tokens recorded per module
│   ├── runner.py             batch runner: hook order, attempts / best-of-N, saving, provenance.json
│   └── check.py              integrity check of a run directory (traceability, costs, eval leakage)
├── analysis/
│   ├── actions.py            action classification (paper's Table 1) and error detection, deterministic rules
│   ├── behavior.py           behavior analysis command; Level 1 profile per run (Table 2, CFG features, P1-P7)
│   ├── compare.py            Level 2: repeated runs of a task compared (sequences, files, patches, metric spread)
│   ├── figures.py            SVG helpers and palette; timelines and similarity heatmap
│   ├── plots.py              the other SVG plots (phases, transitions, errors, outcome, spread, path vs code, ...)
│   ├── patch_view.py         GitHub-style HTML pages comparing every run's patch with the reference fix
│   ├── measures.py           outcome, compute and process measures of one trajectory
│   └── report.py             per-task table, per-condition summary, paired comparisons vs the baseline
├── modules/                  research modules (Requirements, Planning, Testing, Review); registry in __init__.py
├── configs/
│   ├── swelive.yaml          SWE-bench-Live settings, used on top of the built-in swebench.yaml
│   ├── experiments/          one config per experiment (b0.yaml = plain mini baseline)
│   ├── dataset_revision.txt  dataset version of the local copy (written by scripts/download_dataset.py)
│   └── pilot_instances.txt   fixed pilot task list, 10 tasks (written by scripts/make_pilot.py)
├── scripts/
│   ├── check_dataset.py      split size, fields, Docker image names; optionally checks that images exist
│   ├── download_dataset.py   fixed local copy of the dataset (data/, not version-controlled)
│   ├── make_pilot.py         seeded pilot sample, spread over repositories
│   ├── evaluate.sh           SWE-bench-Live evaluation of run folders → <run>/eval/
│   └── smoke.sh              dataset check → gold patches → agent → evaluation, on the first N instances
└── tests/                    equivalence with plain mini, hooks, prompt sections, helper LLM, runner, check
```

Run outputs (`runs/`, `logs/`) are not version-controlled.

## Research layer

The design is frozen as *mini-lab Architecture v1.0*. A module is a dataclass subclass of `Module`; its fields are its
parameters and it overrides only the hooks it needs:

| Hook | When | Returns |
|---|---|---|
| `before_run(ctx)` | before the container starts | nothing (writes artifacts with `ctx.put`) |
| `setup_env(env, ctx)` | after the container starts | nothing |
| `prompt_sections(ctx)` | when the prompt is built | `{name: Add(text, before=None) or Replace(text)}` for `## <name>` sections |
| `before_query(agent, ctx)` | before each model call | messages to inject |
| `on_execute(action, output, ctx)` | after each command | nothing (record only) |
| `transform_output(action, output, ctx)` | after each command | changed output (raw and changed are both logged) |
| `on_submit(patch, ctx)` | when the agent submits | `None` to accept, feedback text to reject (the run continues) |
| `after_run(result, ctx)` | after one attempt | that attempt's result |
| `select_attempt(attempts, ctx)` | once, after all `--attempts` | the chosen attempt |

Modules run in the order Requirements → Planning → Testing → Review (their `category`). At most one module per
experiment may implement `transform_output`, `on_submit` or `select_attempt`. An experiment is a config file that
lists modules by registry name or import path, with their parameters:

```yaml
# minilab/configs/experiments/<name>.yaml, on top of swebench.yaml + minilab/configs/swelive.yaml
minilab:
  modules:
    my_package.my_module.MyModule: {quality: good}
  helper_model: {model_name: openai/gpt-5.1-mini}   # optional; module LLM calls default to the main model
```

Section text is passed to the template as a variable, so module text is never parsed as Jinja. `Add(before="Submission")`
places a new section before an existing one (default: end of the instructions); a missing section is an error.
Modules that need an LLM call `minilab.core.helper_llm.ask(ctx, self.name, prompt)`: a plain completion without
mini's bash tool, with its cost and tokens recorded under the module's name and the prompt and answer logged.

```bash
python -m minilab.core.runner -c swebench.yaml -c minilab/configs/swelive.yaml -c <experiment>.yaml \
  --subset data/SWE-bench-Live --split lite --instances minilab/configs/pilot_instances.txt -w 2
python -m minilab.core.check runs/<model>/<experiment>__<id>/s1 --subset data/SWE-bench-Live --split lite
python -m pytest minilab/tests            # from the repository root
```

### Where runs go

Without `-o`, every run gets a new folder `runs/<model>/<experiment>__<id>/s<k>`, so runs never overwrite each other:

- `<model>`: the last part of `model.model_name` (e.g. `gpt-5.1`), from the merged config;
- `<experiment>`: the name of the config file from `configs/experiments/` (`custom` if there is none);
- `<id>`: a short fingerprint of the whole merged config and the task list. Change anything (model, its settings,
  limits, modules or their parameters, tasks) and the run goes to a new condition folder; the same setup again goes
  to the same condition folder as the next seed (`s1`, `s2`, ...).

`runs/index.jsonl` gets one line per run (folder, model, experiment, modules, tasks, time, git commit). Use `-o <folder>`
only to resume an interrupted run; this is refused if that folder was run with a different config. Prefer a small
config file added last (e.g. `-c minilab/configs/models/<name>.yaml`) over editing `swelive.yaml`, so the shared base
stays the same for every run.

`check` fails a run if `config.json` or `provenance.json` (git commit, mini version, Python, modules) is missing, if a
trajectory's prompt is not the config prompt plus its logged sections, if events or injected messages come from a
module that is not configured, if a helper call has no recorded cost, or (with `--subset`) if a module output contains
an evaluation test file, a FAIL_TO_PASS/PASS_TO_PASS id or a line of the gold patch.

Without a `minilab` section the runner behaves like `mini-extra swebench` (same prompts, commands and patches).
Each trajectory adds `info.minilab` (modules, artifacts, events, costs, tokens), `info.wall_time_seconds` and
`info.base_commit`; unknown
`agent` or `minilab` config keys are errors.

Everything mini-lab puts into a run can be traced to the module that put it there: artifacts record their producer,
hook and step; messages injected by `before_query` carry `extra.minilab = <module name>`; and `info.minilab.events`
logs injected messages, `setup_env` reports, prompt sections added or replaced, helper LLM calls, rejected
submissions and changed command outputs. Everything else in a trajectory comes from mini itself.

## Measuring an experiment

Every condition is measured the same way. A condition is a folder of repeated runs ("seeds") on the same task list:

```bash
python minilab/scripts/download_dataset.py        # once; commit minilab/configs/dataset_revision.txt
python minilab/scripts/make_pilot.py --dataset data/SWE-bench-Live   # 10 tasks; commit pilot_instances.txt
for s in 1 2 3; do                                 # three seeds → runs/gpt-5.1/b0__<id>/s1, s2, s3
  python -m minilab.core.runner -c swebench.yaml -c minilab/configs/swelive.yaml -c minilab/configs/experiments/b0.yaml \
    --subset data/SWE-bench-Live --split lite --instances minilab/configs/pilot_instances.txt -w 4
done
DATASET=data/SWE-bench-Live bash minilab/scripts/evaluate.sh runs/gpt-5.1/b0__*/s*   # → <run>/eval/results.json
python -m minilab.analysis.report runs/gpt-5.1/b0__<id> runs/gpt-5.1/p1__<id> --baseline b0 -o runs/analysis
```

All runs use the local copy, so tasks and tests cannot change between conditions; `provenance.json` records the
dataset, split and version. The same 10 tasks are used for exploration and the pilot, so results on them are
exploratory: they show large effects only, and modules tuned on them look better than they are. For the pilot decision,
grow the list with the same seed (`make_pilot.py ... -n 30`): the 10 tasks stay included, earlier runs still count,
and the 20 new tasks are a fair test.

`report` writes `tasks.csv` (one row per condition, seed and task) and `report.json` (per-condition means and
comparisons), and prints a summary. Measures per task:

| Kind | Measures |
|---|---|
| Outcome | `resolved` (from the evaluation; empty if not evaluated), `submitted`, `exit_status` |
| Compute | `agent_cost`, `helper_cost`, `total_cost` (summed over `--attempts`), `helper_tokens`, `steps`, `wall_time_seconds` |
| Process | `steps_to_first_edit`, `plan_before_first_edit`, `test_commands`, `repro_script`, `git_diff_before_submit`, `rejections` |
| Patch | `files_touched`, `lines_added`, `lines_removed` |

Process measures are heuristics over the commands and the model's text (patterns in `analysis/measures.py`).
Comparisons are paired by task: each task's value is first averaged over seeds (runs of one task are not independent),
then the mean per-task difference (condition − baseline) gets a 95% bootstrap interval over tasks. This is done for
`resolved`, `total_cost` and `steps`. With exactly one seed on both sides, an exact McNemar test on `resolved` is added.

## Behavior analysis (Levels 1 and 2)

A deterministic profile of how the agent behaved in every run, following *Same Signal, Different Semantics: A
Cross-Framework Behavioral Analysis of Software Engineering Agents* (no LLM judgments):

```bash
python -m minilab.analysis.behavior runs/<model>/<condition> [more conditions] -o runs/analysis/behavior
python -m minilab.analysis.behavior runs/<model>/b0__<id> runs/<model>/p1__<id> --baseline b0 -o runs/analysis/p1
```

| Output | Content |
|---|---|
| `level1/run_features.csv` | one row per run: outcome, execution (turns, time, tokens, cost), action counts, error counts by type, timeline, the paper's 16 features, 6 control-flow-graph features, patterns P1-P7, files explored / modified, patch size |
| `level1/action_timelines/<condition>__<seed>__<task>.csv` | one row per turn: category, stage, error type, post-error, repeated, every command part with its rule, return code, tokens, cost, full command |
| `level1/run_reports/<condition>__<seed>__<task>.md` | readable profile of one run (timeline, patterns, errors, files, all features) |
| `level1/classification_audit.csv` | every command part with its category and the rule that matched (for checking the rules by hand) |
| `summary/overall_summary.csv` | per condition and feature: mean, median, range, and means of resolved vs. not resolved runs |
| `summary/thresholds.json` | the medians used for P3, P5 and P6 |
| `level2/pairwise_similarity.csv` | one row per pair of runs of the same task and condition: outcomes, sequence, file and patch similarity |
| `level2/issue_summary.csv` | one row per task: resolved runs, outcome consistency, distinct sequences and patches, mean pairwise similarity, timelines |
| `level2/metric_spread.csv` | per task and behavioral metric: the value of every run, mean, standard deviation, range |
| `level2/issue_comparisons/<condition>__<task>.md` | timelines side by side, metrics per run, pairwise table, files |
| `level2/patch_comparisons/<condition>__<task>.md` | changed lines only in one run of each pair, and every run's patch |
| `summary/level2_summary.csv` | per condition: pairs with the same outcome, identical sequence or patch, mean similarities |
| `level2/changed_line_agreement.csv` | per task: distinct changed lines written by all runs, by some, by one (table behind the agreement figure) |

**Figures** (`summary/figures/`, SVG: open in a browser, hover for values; every value is also printed or in a CSV):

| File | Question |
|---|---|
| `<condition>__timelines.svg` | How did each run go? Every run as a row of turns, colored and lettered by category, errors outlined |
| `<condition>__phases.svg` | Does the agent work in phases? Share of each category by position in the run (10 bins) |
| `<condition>__transitions.svg` | What follows what? Counts of category → next category, with the start and end of runs |
| `<condition>__errors.svg` | What goes wrong? Error turns by type and in how many runs |
| `<condition>__outcome.svg` | Do resolved runs behave differently? Turns, cost, files explored, lines added; one dot per run (descriptive only) |
| `<condition>__spread.svg` | How much do repeated runs vary? Turns and cost of every run per task (separate axes) |
| `<condition>__similarity.svg` | How similar are repeated runs? Tasks x similarity measures |
| `<condition>__path_vs_code.svg` | Does a similar path give similar code? One point per run pair |
| `<condition>__agreement.svg` | How much code do repeated runs share? Changed lines written by all / some / one run |
| `effect__<condition>__vs__<baseline>.svg` | With 2+ conditions: change in solve rate per task, and overall with 95% bootstrap interval |
| `process_shift__<baseline>.svg` | With 2+ conditions: process measures and pattern rates per condition (did the module change the behavior it targets?) |

Colors follow a validated palette (categories: blue, orange, aqua, then grays; magnitudes: one blue ramp); identity
is never carried by color alone (letters, values, shapes, legends). With more than three conditions the process-shift
colors are no longer guaranteed distinguishable for color-blind readers; use `summary/overall_summary.csv` then.

**Turns and categories.** A turn is one model call with its command and result. Commands are split into parts
(`&&`, `||`, `;`, `|`, `&`, newlines; quotes, `$(...)` and here-documents are kept intact). Each part gets one of the
paper's categories (Exploration, Modification, Test, Navigation, Utility, Unknown) by the rules in
`analysis/actions.py`; the turn gets the highest-priority category of its parts:
Modification > Test > Exploration > Utility > Unknown > Navigation. A turn that submits (`COMPLETE_TASK_...`) is Utility.

**Errors.** A turn is an error turn if its return code is non-zero, except `grep`/`rg`/`diff` finding nothing
(code 1 without an error message), or if the output reports a missing command. The type is taken from the end of
the output: `command_not_found`, `timeout`, `syntax_error`, `import_error`, `test_failure`, `file_not_found`,
`permission_denied`, `tool_error`, `traceback`, `usage_error`, `nonzero_exit`.

**Where this differs from the paper** (the paper does not publish these details, or mini needs them):

| Topic | Paper | Here |
|---|---|---|
| Chained commands | one category per action | category per part, turn by priority (above) |
| Python scripts (`python - <<'PY'`) | not specified | write to a repository file → Modification (`python_edit`); write only to `/tmp` → Test (`python_scratch`); otherwise → Test (`python_run`, the agent's reproduction and check scripts). Strict test-runner turns are counted separately (`test_runner_turns`) |
| Scratch files | not specified | writes under `/tmp` are check scripts → Test; `git diff > patch.txt` → Utility (`make_patch`) |
| Linters | not specified | `ruff`, `flake8`, `mypy`, ... → Test (`lint`) |
| Error types | 15 regex types (only examples named) | the 11 types above, with return codes |
| P3, P5, P6 thresholds | medians of the paper's mini-swe-agent runs (not published) | medians over the analysed runs (`summary/thresholds.json`) |
| Phase transition point | "dominant category first shifts" | first turn where the most frequent category so far changes (ties keep the old one), divided by turns |
| Entropies | Shannon entropy | base 2 (bits) |
| Aggregation, PCA, clustering, meta-analysis | per configuration | not done: one profile per run |

**Level 2 measures** (each pair of runs of a task; 1 = identical, 0 = nothing in common):

| Measure | Definition |
|---|---|
| `sequence_similarity` | 1 - edit distance between the two turn-category sequences / length of the longer one |
| `lcs_ratio` | longest common subsequence of the two sequences / length of the longer one |
| `transition_jaccard` | overlap of the sets of consecutive category pairs (which transitions occur at all) |
| `explored_files_jaccard`, `modified_files_jaccard` | overlap of the explored / modified file sets |
| `identical_patch` | same patch after removing `index` lines and trailing whitespace |
| `patch_text_similarity` | `difflib` ratio of the normalized patch lines (includes context lines) |
| `changed_lines_jaccard` | overlap of the added/removed lines (per file, whitespace-trimmed): did the runs write the same code? |
| `touched_lines_jaccard` | overlap of the original-file line numbers covered by the hunks: did they change the same place? |

Navigation is almost never a turn's category in mini, because `cd` is always chained with another command.
Explored files are path-like arguments of exploration commands (approximate); modified files come from the patch.
Check the rules once on a sample of `classification_audit.csv` before relying on them for a new model.

## Patch pages

GitHub-style pages to read and compare the patches of repeated runs, with the reference (gold) fix from the dataset:

```bash
python -m minilab.analysis.patch_view runs/<model>/b0__<id> --subset data/SWE-bench-Live --split lite -o runs/analysis/patches
```

Open `runs/analysis/patches/index.html` in a browser (no internet needed). Each task page has:

| Part | Content |
|---|---|
| Header | repository and **base commit** (links to GitHub), condition, the issue text |
| Summary | per patch (reference fix, then each run): outcome, exit status, turns, cost, files, +/- lines, identical patches, failed tests |
| Patches | each patch as a diff, **Unified** or **Split** view; identical patches are collapsed; every changed line is tagged with how many runs wrote it and `= ref` when the reference fix has it; each file links to its version at the base commit |
| Side by side, per file | all patches that touch a file next to each other |
| Changed lines that differ | for every pair (reference and runs), the changed lines only one of them has |
| Evaluation | the tests that must pass after the fix, the failed tests of each run, and the evaluation test changes |

Without `--subset` the pages have no reference fix or test lists. The reference fix and evaluation tests are shown for
analysis only; modules never see them (`minilab.core.check` checks this).

## Patch files next to other agents

Puts, per task, the patch of each of our runs, the reference (gold) patch and other agents' patches in one folder,
outside `runs/` so it can be committed:

```bash
SUB=https://raw.githubusercontent.com/SWE-bench-Live/submission/main/submissions/lite
for d in tianxicode/deepseek-flash sapient-slingshot-agent/v3.4.0/gpt-5.6-sol agav/gpt-5.5; do
  mkdir -p data/others/$d
  for f in preds.json results.json; do curl -L -o data/others/$d/$f $SUB/$d/$f; done
done
python -m minilab.scripts.compare_patches gpt-6.1-sol \
    --other TianxiCode-DeepSeek-Flash=data/others/tianxicode/deepseek-flash/preds.json \
    --other Sapient-Slingshot-GPT-5.6-Sol=data/others/sapient-slingshot-agent/v3.4.0/gpt-5.6-sol/preds.json \
    --other agav-GPT-5.5=data/others/agav/gpt-5.5/preds.json
```

This writes `patch_diff/compare_gpt-6.1-sol/<instance>/` with `mini-swe-agent_gpt-6.1-sol_run_<k>_patch.diff`,
`reference_patch.diff` and one `<NAME>_patch.diff` per `--other`, plus a `README.md` table of who resolved each task
(from each source's `results.json`). It uses the newest `b0__*` folder of the model (`--experiment` to change);
`--other` can be repeated.

## Changes to the original code

Every change to files outside `minilab/` is listed here.

| File | Change | Why |
|---|---|---|
| `src/minisweagent/run/benchmarks/swebench.py` | Docker image name for instances without an `image_name`/`docker_image` field comes from the config key `run.image_name_template` (Jinja, instance fields available). The default is the original SWE-bench naming, so behaviour without the key is unchanged. | SWE-bench-Live images are named `starryzhang/sweb.eval.x86_64.<id>`, not `swebench/...`. |
| `tests/run/test_swebench.py` | Two tests for the template (direct call and via config). | |

## Setup (Linux)

Requirements: git, Python ≥ 3.10 (3.12 for the evaluator), Docker (your user in the `docker` group), an OpenAI API key.
SWE-bench-Live suggests about 4 CPUs and 16 GB RAM per parallel task, and images need plenty of disk space.

```bash
# 1. This repository
git clone https://github.com/rambodparsi/mini-swe-agent-live.git
cd mini-swe-agent-live
git remote add upstream https://github.com/SWE-agent/mini-swe-agent.git
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
mini-extra config set OPENAI_API_KEY sk-...      # stored outside the repository

# 2. SWE-bench-Live evaluator, next to this repository, in its own environment
git clone --recursive https://github.com/microsoft/SWE-bench-Live.git ../SWE-bench-Live
python3.12 -m venv ../SWE-bench-Live/.venv
../SWE-bench-Live/.venv/bin/pip install -e ../SWE-bench-Live ../SWE-bench-Live/launch

# 3. Check
docker run --rm hello-world
python minilab/scripts/check_dataset.py -n 2 --check-images
```

## Running the baseline (step by step)

All commands run from the repository root (`mini-swe-agent-live/`), with `SWE-bench-Live/` next to it.

### Once

```bash
git checkout main && git pull
source .venv/bin/activate && pip install -e .
python minilab/scripts/download_dataset.py                          # local copy → data/SWE-bench-Live
python minilab/scripts/make_pilot.py --dataset data/SWE-bench-Live  # 10 tasks → minilab/configs/pilot_instances.txt
```

Commit `minilab/configs/dataset_revision.txt` and `minilab/configs/pilot_instances.txt` (both are already in the
repository; do this only when starting from a new dataset version). `data/` and `runs/` are not version-controlled.

### 1. Start a session

Runs take a while, so use `tmux` (the run continues if the connection drops; leave with `Ctrl-b d`, return with
`tmux attach -t b0`). A new terminal or tmux window needs the environment again:

```bash
tmux new -s b0
cd <path>/mini-swe-agent-live && source .venv/bin/activate
git pull
```

### 2. Check the setup with the gold patches (optional, once per machine)

The dataset's correct patches must pass; this checks Docker, the images, the evaluator and the local dataset copy.

```bash
REPO=$PWD
head -2 minilab/configs/pilot_instances.txt > runs_smoke_ids.txt && mkdir -p runs/smoke
(cd ../SWE-bench-Live && .venv/bin/python -m evaluation.evaluation \
  --dataset "$REPO/data/SWE-bench-Live" --split lite --platform linux \
  --patch_dir gold --output_dir "$REPO/runs/smoke/gold" --workers 2 --overwrite 0 \
  --instance_ids $(cat "$REPO/runs_smoke_ids.txt"))
cat runs/smoke/gold/results.json                                    # both IDs under success_ids
```

The evaluator may end with `TypeError: Object of type datetime is not JSON serializable`. This happens after the
results are saved and can be ignored.

### 3. Run the agent: baseline, 3 seeds, 10 tasks

```bash
for s in 1 2 3; do
  python -m minilab.core.runner -c swebench.yaml -c minilab/configs/swelive.yaml -c minilab/configs/experiments/b0.yaml \
    --subset data/SWE-bench-Live --split lite --instances minilab/configs/pilot_instances.txt -w 4
done
```

Each loop iteration is one seed. With the same config the three runs go to the same condition folder as `s1`, `s2`, `s3`.
Each task is capped by `cost_limit` and `step_limit` in `minilab/configs/swelive.yaml`. Lower `-w` if the machine struggles.

### 4. Find the run folder

```bash
cat runs/index.jsonl          # one line per run: output folder, model, experiment, tasks, time, git commit
```

The folder is `runs/<model>/b0__<id>/` (e.g. `runs/gpt-5.1/b0__3fa2c1/`); `<model>` is the last part of `model_name`
and `<id>` changes with any config change. Below, `RUN` stands for that folder:

```bash
RUN=runs/<model>/b0__<id>     # copy it from index.jsonl
cat $RUN/s*/exit_statuses_*.yaml                                   # how each task ended (Submitted, LimitsExceeded, errors)
```

### 5. Check, evaluate, summarize

```bash
for d in $RUN/s*; do python -m minilab.core.check $d --subset data/SWE-bench-Live --split lite; done
DATASET=data/SWE-bench-Live WORKERS=4 bash minilab/scripts/evaluate.sh $RUN/s*
python -m minilab.analysis.report $RUN --baseline b0 -o runs/analysis
```

| Step | What it does | Expected output |
|---|---|---|
| `check` | Each seed folder is complete and traceable; no evaluation tests or gold patch in module outputs | `OK` per seed |
| `evaluate.sh` | Applies every patch in the task's Docker image and runs the task's tests (the slow step) | `Success: X  Failure: Y` per seed; results in `<seed>/eval/results.json` |
| `report` | Combines the seeds into one table and summary | e.g. `b0__3fa2c1: 3 run(s), 10 tasks, resolved 36.7%, cost $0.25/task, 30.1 steps` |

### Outputs

| Path | Content |
|---|---|
| `runs/index.jsonl` | every run: folder, model, experiment, modules, tasks, time, git commit |
| `$RUN/s<k>/config.json`, `provenance.json` | the exact merged config; git commit, dataset version, mini and Python versions |
| `$RUN/s<k>/preds.json` | the agent's patch per task |
| `$RUN/s<k>/<task>/<task>.traj.json` | full trajectory: every model message, command and output (`mini-extra inspect $RUN/s1`) |
| `$RUN/s<k>/exit_statuses_*.yaml` | how each task ended |
| `$RUN/s<k>/eval/results.json`, `eval/<task>/report.json` | resolved / failed tasks, and which tests failed |
| `runs/analysis/tasks.csv`, `report.json` | one row per seed and task; per-condition means and comparisons |

### Changing the model

Prefer a small file added last over editing `swelive.yaml`, so the shared base stays the same and the repository matches
what was run (`provenance.json` records `git_dirty: true` for uncommitted changes):

```yaml
# minilab/configs/models/<name>.yaml
model:
  model_name: anthropic/claude-sonnet-4-5
  model_kwargs: {drop_params: true, parallel_tool_calls: true}
```

```bash
python -m minilab.core.runner ... -c minilab/configs/experiments/b0.yaml -c minilab/configs/models/<name>.yaml ...
```

The run goes to `runs/<new model>/b0__<id>/`; earlier runs are kept. A new provider needs its own key
(`mini-extra config set ANTHROPIC_API_KEY ...`), and `reasoning_effort` is an OpenAI setting.

### Common problems

| Symptom | Cause and fix |
|---|---|
| `missing config.json` / `realpath: 'runs/.../b0__*/s*': No such file` | The path does not exist (e.g. a different model folder). Take the folder from `runs/index.jsonl` |
| `cat: runs_smoke_ids.txt: No such file` | Command run from the wrong folder; `cd` to the repository root first |
| `python: command not found` / wrong packages | Environment not active in this terminal or tmux window: `source .venv/bin/activate` |
| `... was run with a different config` | `-o` points to a folder made with another config; leave out `-o` to get a new folder |
| `git push`: password authentication not supported | Use `gh auth login` (GitHub CLI) or a personal access token, not the account password |
| Docker `permission denied` | `sudo usermod -aG docker $USER`, then log out and in |

## Smoke test (plain mini)

Smoke test on the first 2 instances (from the repository root, with `.venv` active):

```bash
bash minilab/scripts/smoke.sh                   # N=2 WORKERS=2 by default; e.g. N=5 bash minilab/scripts/smoke.sh
```

It writes `runs/smoke_<date>_<time>/`:

| Path | Content |
|---|---|
| `instance_ids.txt` | the instances used |
| `eval_gold/` | evaluator results for the dataset's gold patches (checks the setup) |
| `agent/preds.json` | the agent's patches |
| `agent/<instance_id>/<instance_id>.traj.json` | full trajectory: every model message, command and output |
| `agent/exit_statuses_*.yaml` | how each run ended (`Submitted`, `LimitsExceeded`, errors) |
| `eval_agent/` | evaluator results for the agent's patches; `<instance_id>/report.json` per instance |

The two steps separately:

```bash
mini-extra swebench -c swebench.yaml -c minilab/configs/swelive.yaml \
  --subset SWE-bench-Live/SWE-bench-Live --split lite --slice 0:30 -w 4 -o runs/pilot

cd ../SWE-bench-Live && .venv/bin/python -m evaluation.evaluation \
  --dataset SWE-bench-Live/SWE-bench-Live --split lite --platform linux \
  --patch_dir "$OLDPWD/runs/pilot/preds.json" --output_dir "$OLDPWD/runs/pilot/eval" --workers 4 --overwrite 0
```

Browse trajectories with `mini-extra inspect runs/pilot`.

## License and credit

mini-SWE-agent is MIT-licensed, © 2025 Kilian A. Lieret and Carlos E. Jimenez (see [`LICENSE.md`](../LICENSE.md)).
The license and copyright notice of the original project are kept unchanged.
The SWE-bench-Live dataset and evaluator are by Microsoft (MIT license).

## Citations

```bibtex
@inproceedings{yang2024sweagent,
  title={{SWE}-agent: Agent-Computer Interfaces Enable Automated Software Engineering},
  author={John Yang and Carlos E Jimenez and Alexander Wettig and Kilian Lieret and Shunyu Yao and Karthik R Narasimhan and Ofir Press},
  booktitle={The Thirty-eighth Annual Conference on Neural Information Processing Systems},
  year={2024},
  url={https://arxiv.org/abs/2405.15793}
}

@article{zhang2025swebenchgoeslive,
  title={SWE-bench Goes Live!},
  author={Linghao Zhang and Shilin He and Chaoyun Zhang and Yu Kang and Bowen Li and Chengxing Xie and Junhao Wang and Maoquan Wang and Yufan Huang and Shengyu Fu and Elsie Nallipogu and Qingwei Lin and Yingnong Dang and Saravan Rajmohan and Dongmei Zhang},
  journal={Advances in Neural Information Processing Systems},
  volume={38},
  year={2025}
}

@inproceedings{jimenez2024swebench,
  title={{SWE}-bench: Can Language Models Resolve Real-World {GitHub} Issues?},
  author={Carlos E Jimenez and John Yang and Alexander Wettig and Shunyu Yao and Kexin Pei and Ofir Press and Karthik R Narasimhan},
  booktitle={The Twelfth International Conference on Learning Representations},
  year={2024},
  url={https://openreview.net/forum?id=VTF8yNQM66}
}
```
