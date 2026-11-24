"""Per-task tables over leaderboard submissions: which submission resolved which task, and which has a trajectory.

python -m minilab.scripts.leaderboard_tables patch_diff/mini-swe-agent_vs_leaderboards_preds_and_trajs
# reads <folder>/<submission>/{preds/preds.json, results/results.json, trajs/}
# writes <folder>/resolved_by_instance.csv, trajectories_by_instance.csv and TABLES.md
"""

import csv
import json
import re
from collections import Counter
from pathlib import Path

import typer

app = typer.Typer(add_completion=False)
SYMBOL = {"resolved": "✅", "failed": "❌", "empty": "⬜", "error": "⚠️", "incomplete": "…", "missing": " "}


def statuses(sub: Path) -> dict[str, str]:
    """Status per task; the resolved list wins, then empty patch, error, incomplete, otherwise failed."""
    preds = json.loads((sub / "preds" / "preds.json").read_text())
    r = json.loads((sub / "results" / "results.json").read_text())
    resolved = set(r.get("success_ids") or r.get("resolved_ids") or [])
    errors, incomplete = set(r.get("error_ids", [])), set(r.get("incomplete_ids", []))
    out = {}
    for task, pred in preds.items():
        if task in resolved:
            out[task] = "resolved"
        elif not (pred.get("model_patch") or "").strip():
            out[task] = "empty"
        elif task in errors:
            out[task] = "error"
        elif task in incomplete:
            out[task] = "incomplete"
        else:
            out[task] = "failed"
    return out


def trajectories(sub: Path) -> dict[str, str]:
    """Trajectory format per task: 'folder' for a per-task folder, else the file extension."""
    return {p.name.split(".")[0]: "folder" if p.is_dir() else p.suffix.lstrip(".") for p in (sub / "trajs").iterdir()}


def anchor(heading: str) -> str:
    """GitHub's link target for a heading."""
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def markdown(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows])


@app.command()
def main(
    folder: Path = typer.Argument(..., help="Folder with one subfolder per submission"),
    pairs: list[str] = typer.Option(
        ["tianxicode_deepseek-flash:ami-agent"],
        "--pair",
        help="A:B; lists tasks resolved by A but not B and vice versa",
    ),
) -> None:
    subs = sorted(d for d in folder.iterdir() if (d / "results" / "results.json").exists())
    status = {s.name: statuses(s) for s in subs}
    trajs = {s.name: trajectories(s) for s in subs}
    names = sorted(status, key=lambda n: -sum(v == "resolved" for v in status[n].values()))
    tasks = sorted(set().union(*status.values()))
    n_res = {t: sum(status[n].get(t) == "resolved" for n in names) for t in tasks}

    res_rows = [[t, *(status[n].get(t, "missing") for n in names), str(n_res[t])] for t in tasks]
    traj_rows = [[t, *(trajs[n].get(t, "") for n in names), str(sum(t in trajs[n] for n in names))] for t in tasks]
    for file, rows, last in [
        ("resolved_by_instance.csv", res_rows, "resolved_by"),
        ("trajectories_by_instance.csv", traj_rows, "with_trajectory"),
    ]:
        with (folder / file).open("w", newline="") as f:
            csv.writer(f).writerows([["instance_id", *names, last], *rows])

    total = len(tasks)
    count = {n: Counter(status[n].values()) for n in names}
    res_summary = [["**resolved**", *(f"**{count[n]['resolved']}/{total}**" for n in names), ""]]
    traj_summary = [["**with trajectory**", *(f"**{len(set(trajs[n]) & set(tasks))}/{total}**" for n in names), ""]]
    by_count = {k: sum(v == k for v in n_res.values()) for k in range(len(names) + 1)}
    distribution = ", ".join(f"{k} of {len(names)}: {by_count[k]}" for k in sorted(by_count, reverse=True))
    doc, contents = [], []

    def section(level: int, heading: str, about: str, *lines: str) -> None:
        contents.append(f"{'  ' * (level - 2)}- [{heading}](#{anchor(heading)}): {about}")
        doc.extend([f"{'#' * level} {heading}", "", *lines, ""])

    section(
        2,
        "1. Resolved per task",
        "every task × every submission, with how many submissions resolved each task",
        "Columns are ordered by number of resolved tasks.",
        "",
        markdown(
            ["instance_id", *names, "resolved by"],
            res_summary + [[r[0], *(SYMBOL[c] for c in r[1:-1]), r[-1]] for r in res_rows],
        ),
    )
    section(
        2,
        "2. Trajectory per task",
        "which submission has a trajectory for which task, and in which format",
        "Cell = trajectory format (`folder` = one folder per task, otherwise the file type); empty = no trajectory.",
        "",
        markdown(["instance_id", *names, "with trajectory"], traj_summary + traj_rows),
    )
    note = "Cells show each submission's outcome; `with trajectory` = number of submissions with a trajectory for the task."

    def task_table(chosen: list[str]) -> str:
        return markdown(
            ["#", "instance_id", *names, "with trajectory"],
            [
                [str(i), t, *(SYMBOL[status[n][t]] for n in names), str(sum(t in trajs[n] for n in names))]
                for i, t in enumerate(chosen, 1)
            ],
        )

    for number, title, k, about in [
        (3, "Resolved by all submissions", len(names), "the tasks every submission solved"),
        (4, "Resolved by none", 0, "the tasks no submission solved"),
    ]:
        chosen = [t for t in tasks if n_res[t] == k]
        section(2, f"{number}. {title} ({len(chosen)} tasks)", about, note, "", task_table(chosen))
    for number, pair in enumerate(pairs, 5):
        a, b = pair.split(":")
        if not {a, b} <= set(names):
            raise SystemExit(f"--pair {pair}: unknown submission; choose from {', '.join(names)}")
        section(
            2,
            f"{number}. {a} vs {b}",
            "tasks one of the two resolved and the other did not",
            note + " Not resolved = failed, empty patch or error.",
        )
        for part, (x, y) in zip("ab", [(a, b), (b, a)]):
            chosen = [t for t in tasks if status[x].get(t) == "resolved" and status[y].get(t) != "resolved"]
            section(
                3,
                f"{number}{part}. Resolved by {x}, not by {y} ({len(chosen)} tasks)",
                f"{x} ✅, {y} not",
                task_table(chosen),
            )

    overview = markdown(
        ["submission", "resolved", "failed", "empty patch", "eval. error", "not evaluated", "trajectories", "format"],
        [
            [
                n,
                f"**{count[n]['resolved']}** ({100 * count[n]['resolved'] / total:.1f}%)",
                *(str(count[n][k]) for k in ["failed", "empty", "error", "incomplete"]),
                f"{len(set(trajs[n]) & set(tasks))}/{total}",
                ", ".join(sorted(set(trajs[n].values()))),
            ]
            for n in names
        ],
    )
    header = [
        "# Leaderboard submissions per task",
        "",
        f"How {len(names)} SWE-bench-Live **lite** leaderboard submissions did on each of the {total} tasks, and which of "
        "them published a trajectory. Source, commit and license of the data: [`README.md`](README.md). "
        "Rebuild this page with `python -m minilab.scripts.leaderboard_tables "
        f"{folder}`; the full per-task data is also in `resolved_by_instance.csv` and `trajectories_by_instance.csv`.",
        "",
        "## Summary",
        "",
        overview,
        "",
        f"- Tasks by number of submissions that resolved them: {distribution}.",
        "- Outcomes come from each submission's `results/results.json`; a task in its resolved list counts as resolved, "
        "otherwise it is an empty patch, evaluation error, not evaluated or failed, in that order.",
        "- Legend used in all tables: ✅ resolved · ❌ failed (the patch did not pass the tests) · ⬜ empty patch · "
        "⚠️ evaluation error · … not evaluated.",
        "",
        "## Contents",
        "",
        *contents,
        "",
    ]
    (folder / "TABLES.md").write_text("\n".join(header + doc))
    print(f"{len(tasks)} tasks, {len(names)} submissions → {folder}/TABLES.md")


if __name__ == "__main__":
    app()
