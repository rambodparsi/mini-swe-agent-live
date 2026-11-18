"""Level 2: how different are repeated runs of the same task? Deterministic pairwise comparisons of
action sequences, files and patches, and the spread of behavioral metrics across runs.

A profile is (run_features row, turns) as built by minilab.analysis.behavior; sequences are the turn categories."""

import difflib
import re
from itertools import combinations
from statistics import mean, pstdev

SPREAD_FEATURES = [
    "turns", "cost", "error_turns", "explore_turns", "modify_turns", "test_turns", "test_runner_turns",
    "files_explored", "files_modified", "lines_added", "lines_removed", "exploration_ratio", "modification_ratio",
    "test_ratio", "error_rate", "transition_entropy", "first_modification_timing",
]  # fmt: skip
PAIR_METRICS = [
    "sequence_similarity", "lcs_ratio", "transition_jaccard", "explored_files_jaccard", "modified_files_jaccard",
    "patch_text_similarity", "changed_lines_jaccard", "touched_lines_jaccard",
]  # fmt: skip


def levenshtein(a: list, b: list) -> int:
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def lcs(a: list, b: list) -> int:
    previous = [0] * (len(b) + 1)
    for x in a:
        current = [0]
        for j, y in enumerate(b, 1):
            current.append(previous[j - 1] + 1 if x == y else max(previous[j], current[j - 1]))
        previous = current
    return previous[-1]


def jaccard(a: set, b: set) -> float:
    """Overlap of two sets; two empty sets count as identical."""
    return len(a & b) / len(a | b) if a | b else 1.0


def normalize_patch(patch: str) -> list[str]:
    """Patch lines without `index` lines and trailing whitespace (they differ between identical changes)."""
    return [line.rstrip() for line in patch.splitlines() if line.strip() and not line.startswith("index ")]


def changed_lines(patch: str) -> set[tuple[str, str, str]]:
    """(file, '+'/'-', stripped text) for every added or removed non-blank line."""
    lines, file = set(), ""
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            file = line.split(" b/", 1)[-1]
        elif line[:1] in "+-" and not line.startswith(("+++", "---")) and line[1:].strip():
            lines.add((file, line[0], line[1:].strip()))
    return lines


def touched_lines(patch: str) -> set[tuple[str, int]]:
    """(file, line number in the original file) covered by each hunk: where the change was made."""
    touched, file = set(), ""
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            file = line.split(" b/", 1)[-1]
        elif m := re.match(r"@@ -(\d+)(?:,(\d+))? ", line):
            start, count = int(m.group(1)), int(m.group(2) or 1)
            touched |= {(file, n) for n in range(start, start + max(count, 1))}
    return touched


def split_files(value: str) -> set[str]:
    return set(value.split(";")) - {""} if value else set()


def compare_pair(a: tuple[dict, list], b: tuple[dict, list]) -> dict:
    (ra, ta), (rb, tb) = a, b
    sa, sb = [t.category for t in ta], [t.category for t in tb]
    longest = max(len(sa), len(sb)) or 1
    pa, pb = normalize_patch(ra["patch"]), normalize_patch(rb["patch"])
    return {
        "condition": ra["condition"],
        "instance_id": ra["instance_id"],
        "run_a": ra["seed"],
        "run_b": rb["seed"],
        "resolved_a": ra["resolved"],
        "resolved_b": rb["resolved"],
        "same_outcome": ra["resolved"] == rb["resolved"],
        "turns_a": len(sa),
        "turns_b": len(sb),
        "identical_sequence": sa == sb,
        "edit_distance": levenshtein(sa, sb),
        "sequence_similarity": 1 - levenshtein(sa, sb) / longest,
        "lcs_length": lcs(sa, sb),
        "lcs_ratio": lcs(sa, sb) / longest,
        "transition_jaccard": jaccard(set(zip(sa, sa[1:])), set(zip(sb, sb[1:]))),
        "explored_files_jaccard": jaccard(split_files(ra["explored_files"]), split_files(rb["explored_files"])),
        "modified_files_jaccard": jaccard(split_files(ra["modified_files"]), split_files(rb["modified_files"])),
        "same_modified_files": split_files(ra["modified_files"]) == split_files(rb["modified_files"]),
        "identical_patch": pa == pb,
        "patch_text_similarity": difflib.SequenceMatcher(None, pa, pb, autojunk=False).ratio() if pa or pb else 1.0,
        "changed_lines_jaccard": jaccard(changed_lines(ra["patch"]), changed_lines(rb["patch"])),
        "touched_lines_jaccard": jaccard(touched_lines(ra["patch"]), touched_lines(rb["patch"])),
        "shared_changed_lines": len(changed_lines(ra["patch"]) & changed_lines(rb["patch"])),
    }


def groups(profiles: list[tuple[dict, list]]) -> dict[tuple[str, str], list[tuple[dict, list]]]:
    """Runs of the same task under the same condition, in seed order."""
    by_task: dict[tuple[str, str], list] = {}
    for profile in sorted(profiles, key=lambda p: (p[0]["condition"], p[0]["instance_id"], p[0]["seed"])):
        by_task.setdefault((profile[0]["condition"], profile[0]["instance_id"]), []).append(profile)
    return by_task


def metric_spread(runs: list[tuple[dict, list]]) -> list[dict]:
    rows = []
    for feature in SPREAD_FEATURES:
        values = [r[feature] for r, _ in runs]
        known = [float(v) for v in values if v is not None]
        rows.append({
            "condition": runs[0][0]["condition"], "instance_id": runs[0][0]["instance_id"], "feature": feature,
            **{r["seed"]: v for (r, _), v in zip(runs, values)},
            "mean": mean(known) if known else None, "std": pstdev(known) if known else None,
            "min": min(known, default=None), "max": max(known, default=None),
            "range": max(known) - min(known) if known else None,
        })  # fmt: skip
    return rows


def issue_summary(runs: list[tuple[dict, list]], pairs: list[dict]) -> dict:
    rows = [r for r, _ in runs]
    outcomes = [r["resolved"] for r in rows]
    patches = {tuple(normalize_patch(r["patch"])) for r in rows}
    return {
        "condition": rows[0]["condition"],
        "instance_id": rows[0]["instance_id"],
        "runs": len(rows),
        "resolved_runs": sum(o is True for o in outcomes),
        "outcome_consistent": len(set(outcomes)) == 1,
        "distinct_sequences": len({r["timeline"].replace("!", "") for r in rows}),
        "distinct_patches": len(patches),
        "identical_patch_pairs": sum(p["identical_patch"] for p in pairs),
        **{f"mean_{m}": mean(p[m] for p in pairs) if pairs else None for m in PAIR_METRICS},
        "turns_range": max(r["turns"] for r in rows) - min(r["turns"] for r in rows),
        "timelines": " / ".join(f"{r['seed']}: {r['timeline']}" for r in rows),
    }


def compare_all(profiles: list[tuple[dict, list]]) -> tuple[list[dict], list[dict], list[dict]]:
    """(pairwise rows, per-task summaries, metric spread rows) over every task with at least two runs."""
    pairwise, issues, spread = [], [], []
    for runs in groups(profiles).values():
        if len(runs) < 2:
            continue
        pairs = [compare_pair(a, b) for a, b in combinations(runs, 2)]
        pairwise += pairs
        issues.append(issue_summary(runs, pairs))
        spread += metric_spread(runs)
    return pairwise, issues, spread


def condition_summary(issues: list[dict], pairwise: list[dict]) -> list[dict]:
    out = []
    for condition in dict.fromkeys(i["condition"] for i in issues):
        tasks = [i for i in issues if i["condition"] == condition]
        pairs = [p for p in pairwise if p["condition"] == condition]
        out.append({
            "condition": condition, "tasks": len(tasks), "pairs": len(pairs),
            "outcome_consistent_tasks": sum(i["outcome_consistent"] for i in tasks),
            "same_outcome_pairs": sum(p["same_outcome"] for p in pairs),
            "identical_sequence_pairs": sum(p["identical_sequence"] for p in pairs),
            "identical_patch_pairs": sum(p["identical_patch"] for p in pairs),
            "same_modified_files_pairs": sum(p["same_modified_files"] for p in pairs),
            **{f"mean_{m}": mean(p[m] for p in pairs) for m in PAIR_METRICS},
        })  # fmt: skip
    return out


def fmt(value) -> str:
    return f"{value:.2f}" if isinstance(value, float) else "" if value is None else str(value)


def issue_report(runs: list[tuple[dict, list]], pairs: list[dict], spread: list[dict]) -> str:
    rows = [r for r, _ in runs]
    seeds = [r["seed"] for r in rows]
    outcome = {True: "resolved", False: "not resolved", None: "not evaluated"}
    timelines = "\n".join(f"    {r['seed']:<4} {outcome[r['resolved']]:<14} {r['timeline']}" for r in rows)
    metrics = "\n".join(
        f"| {s['feature']} | " + " | ".join(fmt(s[seed]) for seed in seeds) + f" | {fmt(s['range'])} |" for s in spread
    )
    pair_rows = "\n".join(
        f"| {p['run_a']}-{p['run_b']} | {p['same_outcome']} | {p['edit_distance']} | {fmt(p['sequence_similarity'])} | "
        f"{fmt(p['lcs_ratio'])} | {fmt(p['explored_files_jaccard'])} | {fmt(p['modified_files_jaccard'])} | "
        f"{p['identical_patch']} | {fmt(p['patch_text_similarity'])} | {fmt(p['changed_lines_jaccard'])} | "
        f"{fmt(p['touched_lines_jaccard'])} |"
        for p in pairs
    )
    files = "\n".join(f"| {r['seed']} | {r['modified_files'] or '-'} | {r['explored_files'] or '-'} |" for r in rows)
    return f"""# {rows[0]["instance_id"]} ({rows[0]["condition"]}): {len(rows)} runs

Timelines (E exploration, M modification, T test, N navigation, U utility, ? unknown; ! = error turn):

{timelines}

## Behavioral metrics per run

| Feature | {" | ".join(seeds)} | Range |
|---|{"---|" * len(seeds)}---|
{metrics}

## Pairwise similarity (1 = identical)

| Pair | Same outcome | Edit distance | Sequence sim. | LCS ratio | Explored files | Modified files | Identical patch | Patch text | Changed lines | Patch location |
|---|---|---|---|---|---|---|---|---|---|---|
{pair_rows}

## Files

| Run | Modified | Explored |
|---|---|---|
{files}
"""  # noqa: E501


def patch_report(runs: list[tuple[dict, list]], pairs: list[dict]) -> str:
    rows = [r for r, _ in runs]
    sections = []
    for p in pairs:
        a = next(r for r in rows if r["seed"] == p["run_a"])
        b = next(r for r in rows if r["seed"] == p["run_b"])
        la, lb = changed_lines(a["patch"]), changed_lines(b["patch"])
        only = lambda xs: "\n".join(f"    {f}: {s}{t}" for f, s, t in sorted(xs)) or "    (none)"  # noqa: E731
        sections.append(
            f"### {p['run_a']} vs {p['run_b']}\n\nIdentical: {p['identical_patch']}; "
            f"shared changed lines: {len(la & lb)}; only in {p['run_a']}: {len(la - lb)}; only in {p['run_b']}: {len(lb - la)}\n\n"
            f"Only in {p['run_a']}:\n\n{only(la - lb)}\n\nOnly in {p['run_b']}:\n\n{only(lb - la)}\n"
        )
    patches = "\n".join(f"### {r['seed']} ({r['lines_added']}+ / {r['lines_removed']}-)\n\n```diff\n{r['patch'].rstrip()}\n```\n" for r in rows)  # fmt: skip
    return (
        f"# Patches: {rows[0]['instance_id']} ({rows[0]['condition']})\n\n## Pairwise\n\n"
        + "\n".join(sections)
        + f"\n## Patches\n\n{patches}"
    )
