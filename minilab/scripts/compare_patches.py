"""Collect, per task, the patches of our repeated runs, the reference (gold) patch and other agents' patches.

python -m minilab.scripts.compare_patches gpt-6.1-sol \
    --other TianxiCode-DeepSeek-Flash=path/to/their/preds.json
# writes patch_diff/compare_gpt-6.1-sol/<instance>/{mini-swe-agent_gpt-6.1-sol_run_1_patch.diff, ..., reference_patch.diff,
#   TianxiCode-DeepSeek-Flash_patch.diff} and a README.md with who resolved what
"""

import json
from pathlib import Path

import typer

from minilab.analysis.report import resolved_ids, run_dirs

app = typer.Typer(add_completion=False)


def patches(preds: Path) -> dict[str, str]:
    return {k: v.get("model_patch") or "" for k, v in json.loads(preds.read_text()).items()}


def other_resolved(preds: Path) -> set[str] | None:
    results = preds.parent / "results.json"
    return set(json.loads(results.read_text())["success_ids"]) if results.exists() else None


def condition_dir(runs: Path, model: str, experiment: str) -> Path:
    found = sorted((runs / model).glob(f"{experiment}__*"), key=lambda p: p.stat().st_mtime)
    if not found:
        raise SystemExit(f"No {experiment}__* folder in {runs / model}")
    return found[-1]


def write_compare(
    condition: Path, model: str, gold: dict[str, str], others: dict[str, Path], output: Path
) -> list[str]:
    """Write one folder per task; returns the task ids."""
    ours = {f"mini-swe-agent_{model}_run_{d.name.removeprefix('s')}": d for d in run_dirs(condition)}
    sources = {name: (patches(d / "preds.json"), resolved_ids(d)) for name, d in ours.items()}
    sources |= {name: (patches(p), other_resolved(p)) for name, p in others.items()}
    tasks = sorted({i for name in ours for i in sources[name][0]})
    for task in tasks:
        folder = output / task
        folder.mkdir(parents=True, exist_ok=True)
        for name, (preds, _) in sources.items():
            if task in preds:
                (folder / f"{name}_patch.diff").write_text(preds[task])
        if task in gold:
            (folder / "reference_patch.diff").write_text(gold[task])

    def mark(resolved: set[str] | None, task: str) -> str:
        return "?" if resolved is None else "yes" if task in resolved else "no"

    header = "| Task | " + " | ".join(sources) + " |\n|---|" + "---|" * len(sources) + "\n"
    rows = "".join(f"| {t} | " + " | ".join(mark(r, t) for _, r in sources.values()) + " |\n" for t in tasks)
    (output / "README.md").write_text(
        f"# Patches: mini-swe-agent ({model}) vs reference and other agents\n\n"
        f"Our runs: `{condition}`. Each task folder holds every source's `<name>_patch.diff` and the dataset's "
        "`reference_patch.diff` (gold).\n\nResolved (from each source's evaluation; `?` = no results file):\n\n"
        + header
        + rows
    )
    return tasks


@app.command()
def main(
    model: str = typer.Argument(..., help="Model folder under runs/, e.g. gpt-6.1-sol"),
    other: list[str] = typer.Option([], "--other", help="NAME=path/to/preds.json of another agent (repeatable)"),
    experiment: str = typer.Option("b0", help="Experiment name (newest <experiment>__* folder is used)"),
    runs: Path = typer.Option(Path("runs"), help="Runs folder"),
    dataset: str = typer.Option("data/SWE-bench-Live", help="Dataset for the reference patch"),
    split: str = typer.Option("lite", help="Dataset split"),
    output: Path = typer.Option(Path("patch_diff"), "-o", "--output", help="Parent folder"),
) -> None:
    from datasets import load_dataset

    condition = condition_dir(runs, model, experiment)
    gold = {i["instance_id"]: i["patch"] for i in load_dataset(dataset, split=split)}
    others = {name: Path(path) for name, path in (o.split("=", 1) for o in other)}
    tasks = write_compare(condition, model, gold, others, output / f"compare_{model}")
    print(f"{len(tasks)} task folders from {condition} in {output / f'compare_{model}'}")


if __name__ == "__main__":
    app()
