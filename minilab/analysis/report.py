"""One analysis for every run: per-task table, per-condition summary, and paired comparisons against a baseline.

A condition is a folder of seed runs (`runs/p1/s1`, `runs/p1/s2`, ...) or a single run folder. A run folder holds
`preds.json` and trajectories; its evaluation results are read from `<run>/eval/results.json` (SWE-bench-Live format,
written by minilab/scripts/evaluate.sh).

Usage: python -m minilab.analysis.report runs/b0 runs/p1 --baseline b0 -o runs/analysis
"""

import csv
import json
import math
import random
from pathlib import Path
from statistics import mean

import typer

from minilab.analysis.measures import measure

app = typer.Typer(add_completion=False)
COMPARED = ["resolved", "total_cost", "steps"]


def run_dirs(condition_dir: Path) -> list[Path]:
    if (condition_dir / "preds.json").exists():
        return [condition_dir]
    return sorted(p.parent for p in condition_dir.glob("*/preds.json"))


def resolved_ids(run_dir: Path) -> set[str] | None:
    results = run_dir / "eval" / "results.json"
    return set(json.loads(results.read_text())["success_ids"]) if results.exists() else None


def run_rows(run_dir: Path, condition: str) -> list[dict]:
    """One row per instance: measures of the submitted attempt, cost summed over all attempts."""
    resolved, rows = resolved_ids(run_dir), []
    for instance_id in json.loads((run_dir / "preds.json").read_text()):
        trajs = sorted((run_dir / instance_id).rglob(f"{instance_id}.traj.json"))
        selection = run_dir / instance_id / "selection.json"
        chosen = json.loads(selection.read_text())["chosen"] if selection.exists() else 0
        measured = [measure(json.loads(t.read_text())) for t in trajs]
        row = {"condition": condition, "seed": run_dir.name, "instance_id": instance_id, **measured[chosen]}
        row["attempts"] = len(measured)
        row["agent_cost"] = sum(m["agent_cost"] for m in measured)
        row["helper_cost"] = sum(m["helper_cost"] for m in measured)
        row["total_cost"] = row["agent_cost"] + row["helper_cost"]
        row["resolved"] = None if resolved is None else instance_id in resolved
        rows.append(row)
    return rows


def per_task(rows: list[dict], metric: str) -> dict[str, float]:
    """Mean of `metric` over seeds for each task (seeds of one task are not independent samples)."""
    values: dict[str, list[float]] = {}
    for r in rows:
        if r[metric] is not None:
            values.setdefault(r["instance_id"], []).append(float(r[metric]))
    return {task: mean(v) for task, v in values.items()}


def paired(base: list[dict], treat: list[dict], metric: str, n_boot: int = 10_000) -> dict:
    """Mean per-task difference (treatment - baseline) with a 95% bootstrap CI over tasks."""
    b, t = per_task(base, metric), per_task(treat, metric)
    tasks = sorted(b.keys() & t.keys())
    if not tasks:
        return {"metric": metric, "tasks": 0}
    diffs = [t[k] - b[k] for k in tasks]
    rng = random.Random(0)
    boots = sorted(mean(rng.choices(diffs, k=len(diffs))) for _ in range(n_boot))
    return {
        "metric": metric,
        "tasks": len(tasks),
        "baseline": mean(b[k] for k in tasks),
        "treatment": mean(t[k] for k in tasks),
        "diff": mean(diffs),
        "ci95": [boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]],
    }


def mcnemar(base: list[dict], treat: list[dict]) -> dict:
    """Exact McNemar test on resolved, for one seed per condition."""
    b = {r["instance_id"]: r["resolved"] for r in base if r["resolved"] is not None}
    t = {r["instance_id"]: r["resolved"] for r in treat if r["resolved"] is not None}
    only_base = sum(b[k] and not t[k] for k in b.keys() & t.keys())
    only_treat = sum(t[k] and not b[k] for k in b.keys() & t.keys())
    n = only_base + only_treat
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(only_base, only_treat) + 1)) / 2**n)
    return {"only_baseline": only_base, "only_treatment": only_treat, "p": p}


def summarize(rows: list[dict]) -> dict:
    summary = {"runs": len({r["seed"] for r in rows}), "tasks": len({r["instance_id"] for r in rows})}
    for key in [k for k in rows[0] if k not in ("condition", "seed", "instance_id", "exit_status")]:
        values = [float(r[key]) for r in rows if r[key] is not None]
        summary[key] = mean(values) if values else None
    return summary


def analyze(conditions: dict[str, list[dict]], baseline: str) -> dict:
    report = {"summary": {name: summarize(rows) for name, rows in conditions.items()}, "comparisons": {}}
    for name, rows in conditions.items():
        if name == baseline:
            continue
        base = conditions[baseline]
        comparison = {m: paired(base, rows, m) for m in COMPARED}
        if len({r["seed"] for r in base}) == len({r["seed"] for r in rows}) == 1:
            comparison["mcnemar_resolved"] = mcnemar(base, rows)
        report["comparisons"][name] = comparison
    return report


@app.command()
def main(
    condition_dirs: list[Path] = typer.Argument(..., help="One folder per condition (seed runs inside, or one run)"),
    baseline: str = typer.Option("b0", "--baseline", help="Condition (folder name) to compare against"),
    output: Path = typer.Option(Path("runs/analysis"), "-o", "--output", help="Folder for tasks.csv and report.json"),
) -> None:
    if baseline not in {d.name for d in condition_dirs}:
        raise typer.BadParameter(f"Baseline {baseline!r} is not one of the condition folders")
    conditions = {d.name: [r for run in run_dirs(d) for r in run_rows(run, d.name)] for d in condition_dirs}
    if missing := [name for name, rows in conditions.items() if not rows]:
        raise typer.BadParameter(f"No runs (preds.json) found for {missing}")
    output.mkdir(parents=True, exist_ok=True)
    rows = [r for rs in conditions.values() for r in rs]
    with (output / "tasks.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = analyze(conditions, baseline)
    (output / "report.json").write_text(json.dumps(report, indent=2))
    for name, s in report["summary"].items():
        resolved = "n/a" if s["resolved"] is None else f"{s['resolved']:.1%}"
        print(
            f"{name}: {s['runs']} run(s), {s['tasks']} tasks, resolved {resolved}, cost ${s['total_cost']:.2f}/task, {s['steps']:.1f} steps"
        )
    for name, comparison in report["comparisons"].items():
        for c in comparison.values():
            if "ci95" in c:
                print(
                    f"{name} vs baseline, {c['metric']}: {c['diff']:+.3f} [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] over {c['tasks']} tasks"
                )
    print(f"Wrote {output / 'tasks.csv'} and {output / 'report.json'}")


if __name__ == "__main__":
    app()
