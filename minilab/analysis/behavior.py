"""Behavior analysis of mini-swe-agent trajectories, fully deterministic.
Level 1: one profile per run. Level 2: how repeated runs of the same task differ (minilab/analysis/compare.py).

Features follow "Same Signal, Different Semantics": the 16 features of Table 2, the 6 control-flow-graph features of
§3.3 and the binary patterns P1-P7 of Table 4, computed per run instead of per configuration.

Usage: python -m minilab.analysis.behavior runs/<model>/<condition> [more conditions] -o runs/analysis/behavior
"""

import csv
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

import typer

from minilab.analysis.actions import Part, classify_command, error_type, turn_category
from minilab.analysis.compare import compare_all, condition_summary, groups, issue_report, patch_report
from minilab.analysis.figures import similarity_svg, timelines_svg
from minilab.analysis.measures import patch_stats
from minilab.analysis.plots import (
    SHIFT_MEASURES,
    agreement_rows,
    agreement_svg,
    effect_svg,
    errors_svg,
    outcome_svg,
    path_code_svg,
    phases_svg,
    shift_svg,
    spread_svg,
    transitions_svg,
)
from minilab.analysis.report import paired, per_task, resolved_ids, run_dirs

app = typer.Typer(add_completion=False)
CATEGORIES = ["Exploration", "Modification", "Test", "Navigation", "Utility", "Unknown"]
LETTER = {"Exploration": "E", "Modification": "M", "Test": "T", "Navigation": "N", "Utility": "U", "Unknown": "?"}
WINDOW = 3  # cascade / recovery look-ahead in turns (Table 2)


@dataclass
class Turn:
    index: int
    command: str
    parts: list[Part]
    category: str
    returncode: int | None
    error: str
    output_chars: int
    prompt_tokens: int
    completion_tokens: int
    cost: float


def turns_of(traj: dict) -> list[Turn]:
    """One turn per model call that produced actions; observations are the messages that follow it."""
    messages, turns = traj["messages"], []
    for i, message in enumerate(messages):
        actions = message.get("extra", {}).get("actions") if message.get("role") == "assistant" else None
        if not actions:
            continue
        observations = [m for m in messages[i + 1 : i + 1 + len(actions)] if m.get("role") in ("tool", "user")]
        parts = [p for a in actions for p in classify_command(a.get("command", ""))]
        codes = [o.get("extra", {}).get("returncode") for o in observations]
        errors = [
            error_type(o["extra"].get("raw_output", ""), o["extra"].get("returncode"), o["extra"].get("exception_info", ""), parts)
            for o in observations
            if "returncode" in o.get("extra", {})
        ]  # fmt: skip
        usage = (message["extra"].get("response") or {}).get("usage") or {}
        turns.append(
            Turn(
                index=len(turns) + 1,
                command="\n&& ".join(a.get("command", "") for a in actions),
                parts=parts,
                category=turn_category(parts),
                returncode=next((c for c in codes if c), codes[0] if codes else None),
                error=next((e for e in errors if e), ""),
                output_chars=sum(len(o["extra"].get("raw_output", "")) for o in observations),
                prompt_tokens=usage.get("prompt_tokens") or 0,
                completion_tokens=usage.get("completion_tokens") or 0,
                cost=message["extra"].get("cost") or 0.0,
            )
        )
    return turns


def entropy(items: list) -> float:
    counts, n = Counter(items), len(items)
    return -sum(c / n * math.log2(c / n) for c in counts.values()) if n else 0.0


def cascades(errors: list[bool]) -> list[int]:
    """Lengths of runs of consecutive error turns."""
    runs, length = [], 0
    for e in errors + [False]:
        if e:
            length += 1
        elif length:
            runs.append(length)
            length = 0
    return runs


def phase_transition(categories: list[str]) -> float | None:
    """Normalized index of the first turn at which the most frequent category so far changes (ties keep the old one)."""
    counts, dominant = Counter(), categories[0] if categories else None
    for i, c in enumerate(categories):
        counts[c] += 1
        if counts[c] > counts[dominant]:
            return i / len(categories)
    return None


def table2_features(turns: list[Turn]) -> dict:
    n, cats = len(turns), [t.category for t in turns]
    errors = [bool(t.error) for t in turns]
    commands = [t.command for t in turns]
    repeated = [commands[i] in commands[:i] for i in range(n)]
    error_idx = [i for i, e in enumerate(errors) if e]
    lengths = cascades(errors)
    explore = [i for i, c in enumerate(cats) if c == "Exploration"]
    first_mod = next((i for i, c in enumerate(cats) if c == "Modification"), None)
    late = cats[n - math.ceil(n / 4) :] if n else []
    return {
        **{f"{c.lower()}_ratio": cats.count(c) / n if n else 0.0 for c in CATEGORIES[:4]},
        "utility_ratio": cats.count("Utility") / n if n else 0.0,
        "unknown_ratio": cats.count("Unknown") / n if n else 0.0,
        "trajectory_length": n,
        "trajectory_length_log": math.log1p(n),
        "transition_entropy": entropy(list(zip(cats, cats[1:]))),
        "exploration_frontloading": sum(i < n / 4 for i in explore) / len(explore) if explore else None,
        "first_modification_timing": first_mod / n if first_mod is not None else None,
        "phase_transition_point": phase_transition(cats),
        "late_stage_entropy": entropy(list(zip(late, late[1:]))),
        "error_rate": len(error_idx) / n if n else 0.0,
        "cascade_rate": sum(any(errors[i + 1 : i + 1 + WINDOW]) for i in error_idx) / len(error_idx)
        if error_idx
        else None,
        "recovery_rate": sum(not all(errors[i + 1 : i + 1 + WINDOW]) and i + 1 < n for i in error_idx) / len(error_idx)
        if error_idx
        else None,
        "repetition_rate": sum(repeated) / n if n else 0.0,
        "mean_cascade_length": mean(lengths) if lengths else 0.0,
        "max_cascade_length": max(lengths, default=0),
        "first_cascade_length": lengths[0] if lengths else None,
        "productive_turn_ratio": sum(not e and not r for e, r in zip(errors, repeated)) / n if n else 0.0,
    }


def cfg_features(turns: list[Turn]) -> dict:
    """§3.3: states (category, error context, stage), motifs = consecutive state pairs, edges = consecutive motifs."""
    n = len(turns)
    states = [
        (
            t.category,
            "post_error" if i and turns[i - 1].error else "clean",
            ("early", "mid", "late")[min(2, 3 * i // n)],
        )
        for i, t in enumerate(turns)
    ]
    motifs = list(zip(states, states[1:]))
    edges = list(zip(motifs, motifs[1:]))
    return {
        "motif_entropy": entropy(motifs),
        "cfg_transition_entropy": entropy(edges),
        "self_loop_rate": sum(a == b for a, b in edges) / len(edges) if edges else 0.0,
        "revisit_rate": sum(m in motifs[:i] for i, m in enumerate(motifs)) / len(motifs) if motifs else 0.0,
        "backtrack_rate": sum(motifs[t] == motifs[t - 2] for t in range(2, len(motifs))) / (len(motifs) - 2)
        if len(motifs) > 2
        else 0.0,
        "post_error_motif_ratio": sum("post_error" in (a[1], b[1]) for a, b in motifs) / len(motifs) if motifs else 0.0,
    }


def patterns(row: dict, cats: list[str], medians: dict) -> dict:
    """Table 4. P3, P5 and P6 use medians over the analysed runs (the paper's bash-only medians are not published)."""
    first_mod = next((i for i, c in enumerate(cats) if c == "Modification"), None)
    return {
        "P1_explore_before_modify": None if first_mod is None else "Exploration" in cats[:first_mod],
        "P2_moderate_exploration": 0.30 <= row["exploration_ratio"] <= 0.50,
        "P3_short_cascades": row["max_cascade_length"] < medians["max_cascade_length"],
        "P4_fast_cascade_recovery": None if row["first_cascade_length"] is None else row["first_cascade_length"] <= 2,
        "P5_short_trajectory": row["trajectory_length"] < medians["trajectory_length"],
        "P6_low_late_entropy": row["late_stage_entropy"] < medians["late_stage_entropy"],
        "P7_test_after_modify": first_mod is not None and "Test" in cats[first_mod + 1 :],
    }


def files_of(turns: list[Turn], patch: str) -> dict:
    explored = sorted(
        {p.removeprefix("./").removeprefix("/testbed/") for t in turns for part in t.parts for p in part.paths}
    )
    modified = sorted({line.split(" b/", 1)[1] for line in patch.splitlines() if line.startswith("diff --git ")})
    return {
        "files_explored": len(explored),
        "files_modified": len(modified),
        "modified_files_explored": sum(f in explored for f in modified),
        "explored_files": ";".join(explored),
        "modified_files": ";".join(modified),
    }


def run_profile(traj: dict, condition: str, seed: str, resolved: bool | None) -> tuple[dict, list[Turn]]:
    info, turns = traj["info"], turns_of(traj)
    errors = Counter(t.error for t in turns if t.error)
    row = {
        "condition": condition,
        "seed": seed,
        "instance_id": traj.get("instance_id", ""),
        "resolved": resolved,
        "exit_status": info.get("exit_status", ""),
        "turns": len(turns),
        "duration_seconds": info.get("wall_time_seconds"),
        "prompt_tokens": sum(t.prompt_tokens for t in turns),
        "completion_tokens": sum(t.completion_tokens for t in turns),
        "cost": info.get("model_stats", {}).get("instance_cost", sum(t.cost for t in turns)),
        "explore_turns": sum(t.category == "Exploration" for t in turns),
        "modify_turns": sum(t.category == "Modification" for t in turns),
        "test_turns": sum(t.category == "Test" for t in turns),
        "test_runner_turns": sum(any(p.rule == "test_runner" for p in t.parts) for t in turns),
        "error_turns": sum(bool(t.error) for t in turns),
        **{f"errors_{k}": v for k, v in sorted(errors.items())},
        "timeline": " ".join(LETTER[t.category] + ("!" if t.error else "") for t in turns),
        **table2_features(turns),
        **cfg_features(turns),
        **files_of(turns, info.get("submission", "")),
        **patch_stats(info.get("submission", "")),
        "patch": info.get("submission", ""),  # kept for Level 2; not written to the CSV files
    }
    return row, turns


def trajectory_paths(run_dir: Path) -> list[Path]:
    """The submitted attempt of every instance in preds.json (selection.json picks it when there were several)."""
    paths = []
    for instance_id in json.loads((run_dir / "preds.json").read_text()):
        selection = run_dir / instance_id / "selection.json"
        chosen = json.loads(selection.read_text())["chosen"] if selection.exists() else None
        folder = run_dir / instance_id / (f"attempt_{chosen}" if chosen is not None else "")
        paths.append(folder / f"{instance_id}.traj.json")
    return paths


def collect(condition_dirs: list[Path]) -> list[tuple[dict, list[Turn]]]:
    profiles = []
    for condition_dir in condition_dirs:
        for run_dir in run_dirs(condition_dir):
            resolved = resolved_ids(run_dir)
            for path in trajectory_paths(run_dir):
                traj = json.loads(path.read_text())
                outcome = None if resolved is None else traj.get("instance_id") in resolved
                profiles.append(run_profile(traj, condition_dir.name, run_dir.name, outcome))
    medians = {k: median(row[k] for row, _ in profiles) for k in ("max_cascade_length", "trajectory_length", "late_stage_entropy")} if profiles else {}  # fmt: skip
    error_keys = sorted({k for row, _ in profiles for k in row if k.startswith("errors_")})
    for row, turns in profiles:
        row.update(patterns(row, [t.category for t in turns], medians))
        for key in error_keys:
            row.setdefault(key, 0)
    return profiles


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_name(row: dict) -> str:
    return f"{row['condition']}__{row['seed']}__{row['instance_id']}"


def timeline_rows(turns: list[Turn]) -> list[dict]:
    n, commands = len(turns), [t.command for t in turns]
    return [
        {
            "turn": t.index,
            "category": t.category,
            "stage": ("early", "mid", "late")[min(2, 3 * i // n)],
            "error": t.error,
            "post_error": bool(i and turns[i - 1].error),
            "repeated": t.command in commands[:i],
            "returncode": t.returncode,
            "parts": " | ".join(f"{p.category}:{p.rule}" for p in t.parts),
            "output_chars": t.output_chars,
            "prompt_tokens": t.prompt_tokens,
            "completion_tokens": t.completion_tokens,
            "cost": t.cost,
            "command": t.command,
        }
        for i, t in enumerate(turns)
    ]


def run_report(row: dict, turns: list[Turn]) -> str:
    outcome = {True: "resolved", False: "not resolved", None: "not evaluated"}[row["resolved"]]
    flags = ", ".join(f"{k} = {v}" for k, v in row.items() if k.startswith("P") and k[1].isdigit())
    errors = "\n".join(
        f"| {t.index} | {t.error} | {t.returncode} | `{t.command.splitlines()[0][:90]}` |" for t in turns if t.error
    )
    features = "\n".join(f"| {k} | {v:.3f} |" if isinstance(v, float) else f"| {k} | {v} |" for k, v in row.items()
                         if k not in ("explored_files", "modified_files", "timeline", "patch"))  # fmt: skip
    return f"""# {row["instance_id"]} ({row["condition"]}, {row["seed"]})

Outcome: **{outcome}**, exit status `{row["exit_status"]}`, {row["turns"]} turns, {row["duration_seconds"]} s, ${row["cost"]:.3f}.

Timeline (E exploration, M modification, T test, N navigation, U utility, ? unknown; ! = error turn):

    {row["timeline"]}

Patterns: {flags}

Files modified: {row["modified_files"] or "none"}
Files explored: {row["explored_files"] or "none"}

## Errors

| Turn | Type | Return code | Command (first line) |
|---|---|---|---|
{errors or "| - | - | - | - |"}

## Features

| Feature | Value |
|---|---|
{features}
"""


def summarize(rows: list[dict]) -> list[dict]:
    """Per condition and numeric feature: mean, median, range, and means for resolved vs. not resolved runs."""
    out = []
    for condition in dict.fromkeys(r["condition"] for r in rows):
        group = [r for r in rows if r["condition"] == condition]
        keys = [k for k in dict.fromkeys(k for r in group for k in r)
                if all(isinstance(r.get(k), (bool, int, float, type(None))) for r in group) and k != "resolved"]  # fmt: skip
        for key in keys:
            pairs = [(float(r[key]), r["resolved"]) for r in group if r.get(key) is not None]
            if not pairs:
                continue
            nums = [v for v, _ in pairs]
            by = {o: [v for v, r in pairs if r is o] for o in (True, False)}
            out.append({
                "condition": condition, "feature": key, "runs": len(nums), "mean": mean(nums), "median": median(nums),
                "min": min(nums), "max": max(nums),
                "mean_resolved": mean(by[True]) if by[True] else None,
                "mean_not_resolved": mean(by[False]) if by[False] else None,
            })  # fmt: skip
    return out


def write_level1(profiles: list[tuple[dict, list[Turn]]], output: Path) -> None:
    rows = [{k: v for k, v in row.items() if k != "patch"} for row, _ in profiles]
    write_csv(output / "level1" / "run_features.csv", rows)
    audit = []
    for row, turns in profiles:
        write_csv(output / "level1" / "action_timelines" / f"{run_name(row)}.csv", timeline_rows(turns))
        (output / "level1" / "run_reports").mkdir(parents=True, exist_ok=True)
        (output / "level1" / "run_reports" / f"{run_name(row)}.md").write_text(run_report(row, turns))
        for t in turns:
            for k, p in enumerate(t.parts, 1):
                audit.append({
                    "condition": row["condition"], "seed": row["seed"], "instance_id": row["instance_id"],
                    "turn": t.index, "part": k, "program": p.program, "category": p.category, "rule": p.rule,
                    "turn_category": t.category, "text": p.text[:500],
                })  # fmt: skip
    write_csv(output / "level1" / "classification_audit.csv", audit)
    write_csv(output / "summary" / "overall_summary.csv", summarize(rows))
    thresholds = {
        k: median(r[k] for r in rows) for k in ("max_cascade_length", "trajectory_length", "late_stage_entropy")
    }
    (output / "summary" / "thresholds.json").write_text(json.dumps(thresholds, indent=2))


def write_figures(
    profiles: list[tuple[dict, list[Turn]]], pairwise: list[dict], issues: list[dict], output: Path, baseline: str
) -> None:
    """Every figure: per condition (Levels 1 and 2), and conditions vs. the baseline when there are several."""
    figures = output / "summary" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    by_task = groups(profiles)
    conditions = list(dict.fromkeys(r["condition"] for r, _ in profiles))
    agreement = []
    for condition in conditions:
        mine = [(r, t) for r, t in profiles if r["condition"] == condition]
        rows, runs = [r for r, _ in mine], [t for _, t in mine]
        tasks = [[r for r, _ in group] for (c, _), group in by_task.items() if c == condition]
        turns = {(r["instance_id"], r["seed"]): t for r, t in mine}
        drawings = {
            "timelines": timelines_svg(condition, tasks, turns),
            "phases": phases_svg(condition, runs),
            "transitions": transitions_svg(condition, runs),
            "errors": errors_svg(condition, rows),
            "spread": spread_svg(condition, tasks),
        }
        if any(r["resolved"] is not None for r in rows):
            drawings["outcome"] = outcome_svg(condition, rows)
        if condition_pairs := [p for p in pairwise if p["condition"] == condition]:
            drawings["similarity"] = similarity_svg(condition, [i for i in issues if i["condition"] == condition])
            drawings["path_vs_code"] = path_code_svg(condition, condition_pairs)
            repeated = [group for group in tasks if len(group) > 1]
            agreement += agreement_rows(repeated)
            drawings["agreement"] = agreement_svg(condition, agreement_rows(repeated))
        for name, drawing in drawings.items():
            (figures / f"{condition}__{name}.svg").write_text(drawing)
    if agreement:
        write_csv(output / "level2" / "changed_line_agreement.csv", agreement)
    if len(conditions) < 2:
        return
    rows = [r for r, _ in profiles]
    base = [r for r in rows if r["condition"] == baseline]
    means = {
        c: {key: mean([float(r[key]) for r in rows if r["condition"] == c and r.get(key) is not None] or [math.nan])
            for key, _ in SHIFT_MEASURES}
        for c in conditions
    }  # fmt: skip
    means = {c: {k: (None if math.isnan(v) else v) for k, v in m.items()} for c, m in means.items()}
    (figures / f"process_shift__{baseline}.svg").write_text(shift_svg([baseline] + [c for c in conditions if c != baseline], means))  # fmt: skip
    for condition in conditions:
        treated = [r for r in rows if r["condition"] == condition]
        overall = paired(base, treated, "resolved")
        if condition == baseline or not overall["tasks"]:
            continue
        b, t = per_task(base, "resolved"), per_task(treated, "resolved")
        diffs = [(task, t[task] - b[task]) for task in sorted(b.keys() & t.keys())]
        (figures / f"effect__{condition}__vs__{baseline}.svg").write_text(
            effect_svg(baseline, condition, diffs, overall)
        )


def write_level2(
    profiles: list[tuple[dict, list[Turn]]], pairwise: list[dict], issues: list[dict], spread: list[dict], output: Path
) -> list[dict]:
    by_task = groups(profiles)
    if not pairwise:
        return []
    write_csv(output / "level2" / "pairwise_similarity.csv", pairwise)
    write_csv(output / "level2" / "issue_summary.csv", issues)
    write_csv(output / "level2" / "metric_spread.csv", spread)
    summary = condition_summary(issues, pairwise)
    write_csv(output / "summary" / "level2_summary.csv", summary)
    for folder in ("issue_comparisons", "patch_comparisons"):
        (output / "level2" / folder).mkdir(parents=True, exist_ok=True)
    for (condition, instance), runs in by_task.items():
        pairs = [p for p in pairwise if (p["condition"], p["instance_id"]) == (condition, instance)]
        if not pairs:
            continue
        task_spread = [s for s in spread if (s["condition"], s["instance_id"]) == (condition, instance)]
        name = f"{condition}__{instance}.md"
        (output / "level2" / "issue_comparisons" / name).write_text(issue_report(runs, pairs, task_spread))
        (output / "level2" / "patch_comparisons" / name).write_text(patch_report(runs, pairs))
    return summary


def baseline_name(condition_dirs: list[Path], baseline: str) -> str:
    names = [d.name for d in condition_dirs]
    matches = [n for n in names if baseline in (n, n.split("__")[0])]
    if len(names) > 1 and len(matches) != 1:
        raise typer.BadParameter(f"Baseline {baseline!r} must match exactly one condition folder, matched {matches}")
    return matches[0] if matches else names[0]


@app.command()
def main(
    condition_dirs: list[Path] = typer.Argument(..., help="Condition folders (seed runs inside) or single run folders"),
    output: Path = typer.Option(Path("runs/analysis/behavior"), "-o", "--output", help="Output folder"),
    baseline: str = typer.Option(
        "b0",
        "--baseline",
        help="Condition to compare against (folder name, or its part before '__'); used with 2+ conditions",
    ),
) -> None:
    baseline = baseline_name(condition_dirs, baseline)
    profiles = collect(condition_dirs)
    if not profiles:
        raise typer.BadParameter("No runs (preds.json) found")
    pairwise, issues, spread = compare_all(profiles)
    write_level1(profiles, output)
    summary = write_level2(profiles, pairwise, issues, spread, output)
    write_figures(profiles, pairwise, issues, output, baseline)
    rows = [row for row, _ in profiles]
    parts = [p for _, turns in profiles for t in turns for p in t.parts]
    unknown = sum(p.category == "Unknown" for p in parts)
    print(f"{len(rows)} runs, {sum(r['turns'] for r in rows)} turns, {len(parts)} command parts ({unknown} unknown)")
    for c in CATEGORIES:
        print(f"  {c:<12} {mean(r[c.lower() + '_ratio'] for r in rows):.1%} of turns")
    for c in summary:
        print(
            f"{c['condition']}: {c['tasks']} tasks, {c['pairs']} run pairs; same outcome in {c['same_outcome_pairs']} pairs, "
            f"identical action sequence in {c['identical_sequence_pairs']}, identical patch in {c['identical_patch_pairs']}; "
            f"mean sequence similarity {c['mean_sequence_similarity']:.2f}, patch text similarity {c['mean_patch_text_similarity']:.2f}"
        )
    print(f"Wrote {output / 'level1'}, {output / 'level2'} and {output / 'summary'} (figures in summary/figures)")


if __name__ == "__main__":
    app()
