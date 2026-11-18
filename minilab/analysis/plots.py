"""Analysis plots as static, deterministic SVG (see figures.py for the shared palette and helpers).

Level 1: where actions happen in a run, action transitions, errors by type, resolved vs. not resolved runs.
Level 2: spread of repeated runs, path vs. code similarity, agreement on changed lines.
Conditions: effect on resolution vs. the baseline, and process shift. One measure per axis; every value is
printed or available in a CSV table and as a hover title."""

import math
from collections import Counter
from html import escape

from minilab.analysis.compare import changed_lines
from minilab.analysis.figures import FILL, GRID, INK, INK_2, LETTER, RAMP, SURFACE, svg, text

CATEGORIES = ["Exploration", "Modification", "Test", "Utility", "Navigation", "Unknown"]
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
ORDINAL = ["#184f95", "#3987e5", "#86b6ef"]  # all runs / some runs / one run (ordinal steps 600, 400, 250)
BINS = 10


def header(title: str, subtitle: str) -> list[str]:
    return [text(16, 20, title, 15, weight=600), text(16, 40, subtitle, 12, INK_2)]


def nice_ticks(value: float) -> list[float]:
    """Round tick values from 0 up to at least `value`: steps of 1, 2 or 5 x 10^n, at most 6 ticks."""
    if value <= 0:
        return [0.0, 0.25, 0.5, 0.75, 1.0]
    raw = value / 4
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= raw)
    return [round(k * step, 10) for k in range(math.ceil(value / step - 1e-9) + 1)]


def tick_label(value: float, money: bool = False) -> str:
    label = f"{value:.3g}"
    return f"${label}" if money else label


def swarm(ys: list[float], radius: float = 4.5) -> list[float]:
    """Horizontal offsets so dots at nearby heights sit side by side instead of on top of each other."""
    placed: list[tuple[float, float]] = []
    for y in ys:
        candidates = [0.0] + [k * sign * (radius * 2 + 1) for k in range(1, 20) for sign in (1, -1)]
        dx = next(
            c for c in candidates if all((c - px) ** 2 + (y - py) ** 2 >= (radius * 2 + 1) ** 2 for px, py in placed)
        )
        placed.append((dx, y))
    return [dx for dx, _ in placed]


def ramp(share: float) -> tuple[str, str]:
    """Cell fill on the sequential ramp and the ink that stays readable on it."""
    step = round(max(0.0, min(1.0, share)) * (len(RAMP) - 1))
    return RAMP[step], SURFACE if step >= 7 else INK


def cell(x: float, y: float, w: float, h: float, fill: str, label: str, tip: str, ink: str = INK) -> list[str]:
    return [
        f'<g><title>{escape(tip)}</title><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}"/>',
        text(x + w / 2, y + h / 2, label, 11, ink, "middle") + "</g>",
    ]


def present(categories: list[str]) -> list[str]:
    return [c for c in CATEGORIES if c in categories or c in ("Exploration", "Modification", "Test", "Utility")]


# Level 1


def phases_svg(condition: str, runs: list[list]) -> str:
    """Share of turns in each category by position in the run (10 equal bins of normalized turn index)."""
    counts = [Counter() for _ in range(BINS)]
    for turns in runs:
        for i, t in enumerate(turns):
            counts[min(BINS - 1, i * BINS // len(turns))][t.category] += 1
    rows = present([c for bin_ in counts for c in bin_])
    cw, ch, left, top = 62, 30, 150, 92
    body = header(
        f"Where actions happen in a run: {condition}",
        f"Share of turns in each part of the run, over {len(runs)} runs; columns sum to 100%",
    )
    for b in range(BINS):
        x = left + b * (cw + 2)
        body.append(text(x + cw / 2, top - 30, f"{b * 10}-{(b + 1) * 10}%", 11, INK_2, "middle"))
        body.append(text(x + cw / 2, top - 14, f"n={sum(counts[b].values())}", 10, INK_2, "middle"))
    for r, category in enumerate(rows):
        y = top + r * (ch + 2)
        body.append(f'<rect x="16" y="{y + ch / 2 - 6}" width="12" height="12" rx="3" fill="{FILL[category]}"/>')
        body.append(text(34, y + ch / 2, f"{LETTER[category]} {category}", 12))
        for b in range(BINS):
            total = sum(counts[b].values())
            share = counts[b][category] / total if total else 0.0
            fill, ink = ramp(share)
            tip = f"{category}, {b * 10}-{(b + 1) * 10}% of the run: {counts[b][category]} of {total} turns"
            body += cell(left + b * (cw + 2), y, cw, ch, fill, f"{share:.0%}", tip, ink)
    y = top + len(rows) * (ch + 2) + 18
    body.append(text(left, y, "position in the run (share of its turns) →", 11, INK_2))
    return svg(left + BINS * (cw + 2) + 16, y + 18, body, f"Where actions happen in a run for {condition}")


def transitions_svg(condition: str, runs: list[list]) -> str:
    """Counts of 'this turn → next turn' category pairs, with the first and last turn of every run."""
    pairs = Counter()
    for turns in runs:
        cats = ["start"] + [t.category for t in turns] + ["end"]
        pairs.update(zip(cats, cats[1:]))
    used = present([c for pair in pairs for c in pair])
    sources, targets = ["start"] + used, used + ["end"]
    peak = max(pairs.values(), default=1)
    cw, ch, left, top = 84, 30, 170, 104
    body = header(
        f"Action transitions: {condition}", f"How often a turn of one kind follows another, over {len(runs)} runs"
    )
    body.append(text(left + len(targets) * (cw + 2) / 2, top - 44, "next turn →", 11, INK_2, "middle"))
    for c, target in enumerate(targets):
        body.append(text(left + c * (cw + 2) + cw / 2, top - 20, target if target == "end" else f"{LETTER[target]} {target}", 11, INK_2, "middle"))  # fmt: skip
    body.append(text(16, top - 20, "this turn ↓", 11, INK_2))
    for r, source in enumerate(sources):
        y = top + r * (ch + 2)
        body.append(text(16, y + ch / 2, source if source == "start" else f"{LETTER[source]} {source}", 12))
        for c, target in enumerate(targets):
            n = pairs[(source, target)]
            fill, ink = ramp(n / peak) if n else (GRID, INK_2)
            body += cell(left + c * (cw + 2), y, cw, ch, fill, str(n), f"{source} → {target}: {n}", ink)
    height = top + len(sources) * (ch + 2) + 16
    return svg(left + len(targets) * (cw + 2) + 16, height, body, f"Action transitions for {condition}")


def bars(rows: list[tuple[str, float, str]], left: int, top: int, width: int, money: bool = False) -> list[str]:
    """Horizontal bars from a zero baseline, 4px rounded data end, value printed after the bar."""
    ticks, body, bh = nice_ticks(max((v for _, v, _ in rows), default=1)), [], 22
    peak = ticks[-1]
    for tick in ticks:
        x = left + width * tick / peak
        body.append(f'<line x1="{x}" y1="{top - 6}" x2="{x}" y2="{top + len(rows) * (bh + 8)}" stroke="{GRID}"/>')
        body.append(text(x, top + len(rows) * (bh + 8) + 12, tick_label(tick, money), 10, INK_2, "middle"))
    for r, (label, value, note) in enumerate(rows):
        y, w = top + r * (bh + 8), max(2.0, width * value / peak)
        body.append(text(left - 10, y + bh / 2, label, 12, INK, "end"))
        body.append(f'<g><title>{escape(f"{label}: {value:g} {note}")}</title>'
                    f'<path d="M{left},{y} h{w - 4} a4,4 0 0 1 4,4 v{bh - 8} a4,4 0 0 1 -4,4 h{-(w - 4)} z" fill="{SERIES[0]}"/></g>')  # fmt: skip
        body.append(text(left + w + 8, y + bh / 2, f"{value:g}  {note}", 11, INK_2))
    return body


def errors_svg(condition: str, rows: list[dict]) -> str:
    """Error turns by type, with the number of runs in which each type occurs."""
    totals = Counter()
    runs_with = Counter()
    for r in rows:
        for key, value in r.items():
            if key.startswith("errors_") and value:
                totals[key[7:]] += int(value)
                runs_with[key[7:]] += 1
    items = [(name, n, f"in {runs_with[name]} of {len(rows)} runs") for name, n in totals.most_common()]
    left, top = 190, 70
    body = header(f"Error turns by type: {condition}", f"{sum(totals.values())} error turns in {len(rows)} runs")
    body += bars(items or [("no errors", 0, "")], left, top, 420)
    return svg(left + 420 + 150, top + max(1, len(items)) * 30 + 34, body, f"Error turns by type for {condition}")


OUTCOME_MEASURES = [("turns", "Turns", False), ("cost", "Cost per run", True),
                    ("files_explored", "Files explored", False), ("lines_added", "Lines added", False)]  # fmt: skip


def outcome_svg(condition: str, rows: list[dict]) -> str:
    """Small multiples: each run as a dot, resolved vs. not resolved, with the group mean as a line."""
    groups = [(True, "resolved"), (False, "not resolved")]
    evaluated = [r for r in rows if r["resolved"] is not None]
    pw, ph, top, gap = 230, 260, 84, 26
    body = header(
        f"Resolved vs. not resolved runs: {condition}",
        f"One dot per run ({sum(r['resolved'] is True for r in evaluated)} resolved, "
        f"{sum(r['resolved'] is False for r in evaluated)} not); line = group mean. Few runs: descriptive only",
    )
    for p, (key, title, money) in enumerate(OUTCOME_MEASURES):
        x0 = 16 + p * (pw + gap)
        ticks = nice_ticks(max((float(r[key]) for r in evaluated), default=1))
        y_of = lambda v, peak=ticks[-1]: top + 24 + (ph - 60) * (1 - v / peak)  # noqa: E731
        body.append(text(x0, top, title, 13, weight=600))
        for tick in ticks:
            body.append(f'<line x1="{x0 + 44}" y1="{y_of(tick)}" x2="{x0 + pw}" y2="{y_of(tick)}" stroke="{GRID}"/>')
            body.append(text(x0 + 38, y_of(tick), tick_label(tick, money), 10, INK_2, "end"))
        for g, (outcome, label) in enumerate(groups):
            cx = x0 + 44 + (pw - 44) * (g + 0.5) / 2
            values = sorted(float(r[key]) for r in evaluated if r["resolved"] is outcome)
            if values:  # mean line first, so the dots stay on top of it
                m = sum(values) / len(values)
                body.append(f'<line x1="{cx - 26}" y1="{y_of(m)}" x2="{cx + 26}" y2="{y_of(m)}" stroke="{INK}" stroke-width="2"/>')  # fmt: skip
            for v, offset in zip(values, swarm([y_of(v) for v in values])):
                body.append(f'<g><title>{escape(f"{label}: {tick_label(v, money)}")}</title><circle cx="{cx + offset}" '
                            f'cy="{y_of(v)}" r="4.5" fill="{SERIES[g]}" stroke="{SURFACE}" stroke-width="2"/></g>')  # fmt: skip
            body.append(text(cx, top + ph - 18, label, 11, INK_2, "middle"))
            body.append(text(cx, top + ph - 4, f"n={len(values)}", 10, INK_2, "middle"))
            if values:
                body.append(
                    text(cx, top + ph + 10, f"mean {tick_label(sum(values) / len(values), money)}", 10, INK_2, "middle")
                )
    return svg(16 + 4 * (pw + gap), top + ph + 26, body, f"Resolved vs. not resolved runs for {condition}")


# Level 2


def spread_svg(condition: str, tasks: list[list[dict]]) -> str:
    """Per task, the value of every run (dot) and their range (line), for turns and for cost: two panels, two axes."""
    measures = [("turns", "Turns", False), ("cost", "Cost per run", True)]
    pw, rh, left, top, gap = 300, 26, 230, 104, 80
    body = header(
        f"Spread of repeated runs: {condition}",
        "Each dot is one run (filled = resolved, hollow = not resolved); the line spans the runs of a task",
    )
    for p, (key, title, money) in enumerate(measures):
        x0 = left + p * (pw + gap)
        ticks = nice_ticks(max((float(r[key]) for runs in tasks for r in runs), default=1))
        x_of = lambda v, x0=x0, peak=ticks[-1]: x0 + pw * v / peak  # noqa: E731
        body.append(text(x0, top - 40, title, 13, weight=600))
        for tick in ticks:
            x = x_of(tick)
            body.append(f'<line x1="{x}" y1="{top - 14}" x2="{x}" y2="{top + len(tasks) * rh}" stroke="{GRID}"/>')
            body.append(text(x, top - 22, tick_label(tick, money), 10, INK_2, "middle"))
        for t, runs in enumerate(tasks):
            y = top + t * rh + rh / 2
            values = [float(r[key]) for r in runs]
            body.append(f'<line x1="{x_of(min(values))}" y1="{y}" x2="{x_of(max(values))}" y2="{y}" stroke="{INK_2}" stroke-width="2"/>')  # fmt: skip
            for r in runs:
                fill = SERIES[0] if r["resolved"] else SURFACE
                tip = f"{r['instance_id']} {r['seed']}: {tick_label(float(r[key]), money)}"
                body.append(f'<g><title>{escape(tip)}</title><circle cx="{x_of(float(r[key]))}" cy="{y}" r="5" '
                            f'fill="{fill}" stroke="{SERIES[0]}" stroke-width="2"/></g>')  # fmt: skip
    for t, runs in enumerate(tasks):
        body.append(text(16, top + t * rh + rh / 2, runs[0]["instance_id"], 12))
    return svg(left + 2 * (pw + gap), top + len(tasks) * rh + 16, body, f"Spread of repeated runs for {condition}")


def path_code_svg(condition: str, pairwise: list[dict]) -> str:
    """One point per pair of runs: similar path (x) vs. similar code (y); shape = same or different outcome."""
    size, left, top = 380, 70, 84
    body = header(
        f"Similar path, similar code? {condition}",
        "One point per pair of runs of the same task; circle = same outcome, square = different outcome",
    )
    x_of = lambda v: left + size * v  # noqa: E731
    y_of = lambda v: top + size * (1 - v)  # noqa: E731
    for k in range(5):
        v = k / 4
        body.append(f'<line x1="{x_of(v)}" y1="{top}" x2="{x_of(v)}" y2="{top + size}" stroke="{GRID}"/>')
        body.append(f'<line x1="{left}" y1="{y_of(v)}" x2="{left + size}" y2="{y_of(v)}" stroke="{GRID}"/>')
        body.append(text(x_of(v), top + size + 14, f"{v:g}", 10, INK_2, "middle"))
        body.append(text(left - 8, y_of(v), f"{v:g}", 10, INK_2, "end"))
    body.append(text(left + size / 2, top + size + 34, "action-sequence similarity (1 = same order of actions)", 11, INK_2, "middle"))  # fmt: skip
    body.append(f'<text x="18" y="{top + size / 2}" font-size="11" fill="{INK_2}" text-anchor="middle" '
                f'transform="rotate(-90 18 {top + size / 2})">changed-lines overlap (1 = same code)</text>')  # fmt: skip
    for p in sorted(pairwise, key=lambda p: (p["instance_id"], p["run_a"], p["run_b"])):
        x, y = x_of(p["sequence_similarity"]), y_of(p["changed_lines_jaccard"])
        tip = (f"{p['instance_id']} {p['run_a']}-{p['run_b']}: sequence {p['sequence_similarity']:.2f}, "
               f"changed lines {p['changed_lines_jaccard']:.2f}, same outcome {p['same_outcome']}")  # fmt: skip
        mark = (f'<circle cx="{x}" cy="{y}" r="5"' if p["same_outcome"] else f'<rect x="{x - 5}" y="{y - 5}" width="10" height="10" rx="1"')  # fmt: skip
        body.append(f'<g><title>{escape(tip)}</title>{mark} fill="{SERIES[0] if p["same_outcome"] else SERIES[1]}" '
                    f'stroke="{SURFACE}" stroke-width="2"/></g>')  # fmt: skip
    legend_x = left + size + 24
    body.append(f'<circle cx="{legend_x + 6}" cy="{top + 10}" r="5" fill="{SERIES[0]}"/>')
    body.append(text(legend_x + 18, top + 10, f"same outcome ({sum(p['same_outcome'] for p in pairwise)})", 11, INK_2))
    body.append(f'<rect x="{legend_x + 1}" y="{top + 29}" width="10" height="10" rx="1" fill="{SERIES[1]}"/>')
    body.append(text(legend_x + 18, top + 34, f"different outcome ({sum(not p['same_outcome'] for p in pairwise)})", 11, INK_2))  # fmt: skip
    return svg(legend_x + 190, top + size + 50, body, f"Path vs. code similarity for {condition}")


def agreement_rows(tasks: list[list[dict]]) -> list[dict]:
    """Per task: changed lines written by all runs, by some, by only one (the table behind agreement_svg)."""
    out = []
    for runs in tasks:
        counts = Counter(line for r in runs for line in changed_lines(r["patch"]))
        n = len(runs)
        out.append({
            "condition": runs[0]["condition"], "instance_id": runs[0]["instance_id"], "runs": n,
            "resolved_runs": sum(r["resolved"] is True for r in runs), "changed_lines": len(counts),
            "in_all_runs": sum(c == n for c in counts.values()),
            "in_some_runs": sum(1 < c < n for c in counts.values()),
            "in_one_run": sum(c == 1 for c in counts.values()),
        })  # fmt: skip
    return out


def agreement_svg(condition: str, rows: list[dict]) -> str:
    """Stacked bars per task: distinct changed lines by how many runs wrote them (2px gaps between segments)."""
    parts = [
        ("in_all_runs", "written by all runs"),
        ("in_some_runs", "by some runs"),
        ("in_one_run", "by one run only"),
    ]
    left, top, width, bh = 230, 96, 460, 22
    ticks = nice_ticks(max((r["changed_lines"] for r in rows), default=1))
    peak = ticks[-1]
    body = header(
        f"How much of the code do repeated runs agree on? {condition}",
        "Distinct added or removed lines per task, by how many of its runs wrote them",
    )
    x = left
    for k, (_, label) in enumerate(parts):
        body.append(f'<rect x="{x}" y="{top - 44}" width="14" height="14" rx="3" fill="{ORDINAL[k]}"/>')
        body.append(text(x + 20, top - 37, label, 11, INK_2))
        x += 40 + 7 * len(label)
    for tick in ticks:
        gx = left + width * tick / peak
        body.append(f'<line x1="{gx}" y1="{top - 8}" x2="{gx}" y2="{top + len(rows) * (bh + 8)}" stroke="{GRID}"/>')
        body.append(text(gx, top + len(rows) * (bh + 8) + 12, tick_label(tick), 10, INK_2, "middle"))
    for i, r in enumerate(rows):
        y, x = top + i * (bh + 8), float(left)
        body.append(text(16, y + bh / 2, r["instance_id"], 12))
        for k, (key, label) in enumerate(parts):
            w = width * r[key] / peak
            if r[key]:
                tip = f"{r['instance_id']}: {r[key]} lines {label}"
                body.append(f'<g><title>{escape(tip)}</title><rect x="{x}" y="{y}" width="{max(w - 2, 1)}" height="{bh}" '
                            f'rx="{3 if k == 2 else 0}" fill="{ORDINAL[k]}"/></g>')  # fmt: skip
                if w > 26:
                    body.append(text(x + (w - 2) / 2, y + bh / 2, str(r[key]), 10, SURFACE if k < 2 else INK, "middle"))
            x += w
        body.append(text(x + 8, y + bh / 2, f"{r['changed_lines']} lines, {r['resolved_runs']}/{r['runs']} resolved", 11, INK_2))  # fmt: skip
    return svg(left + width + 200, top + len(rows) * (bh + 8) + 30, body, f"Agreement on changed lines for {condition}")


# Conditions vs. baseline


def effect_svg(baseline: str, condition: str, per_task: list[tuple[str, float]], overall: dict) -> str:
    """Per task: change in solve rate (condition - baseline, averaged over seeds); overall: mean with 95% CI."""
    left, top, width, rh = 230, 84, 420, 26
    x_of = lambda v: left + width * (v + 1) / 2  # noqa: E731
    body = header(
        f"Effect on resolution: {condition} vs. {baseline}",
        "Change in solve rate per task (seeds averaged); bottom row: mean over tasks with 95% bootstrap interval",
    )
    rows = per_task + [("All tasks", overall["diff"])]
    bottom = top + len(rows) * rh + 8
    for v in (-1, -0.5, 0, 0.5, 1):
        stroke = INK_2 if v == 0 else GRID
        body.append(f'<line x1="{x_of(v)}" y1="{top - 8}" x2="{x_of(v)}" y2="{bottom}" stroke="{stroke}"/>')
        body.append(text(x_of(v), bottom + 12, f"{v:+g}" if v else "0", 10, INK_2, "middle"))
    body.append(text(x_of(-1), top - 18, f"← worse than {baseline}", 11, INK_2))
    body.append(text(x_of(1), top - 18, f"better than {baseline} →", 11, INK_2, "end"))
    for i, (task, diff) in enumerate(rows):
        y = top + i * rh + rh / 2 + (8 if task == "All tasks" else 0)
        body.append(text(16, y, task, 12, weight=600 if task == "All tasks" else 400))
        if task == "All tasks":
            lo, hi = overall["ci95"]
            body.append(f'<line x1="{x_of(lo)}" y1="{y}" x2="{x_of(hi)}" y2="{y}" stroke="{INK}" stroke-width="2"/>')
            label = f"{diff:+.2f} [{lo:+.2f}, {hi:+.2f}]"
        else:
            label = f"{diff:+.2f}"
        body.append(f'<g><title>{escape(f"{task}: {label}")}</title><circle cx="{x_of(diff)}" cy="{y}" r="5.5" '
                    f'fill="{SERIES[0]}" stroke="{SURFACE}" stroke-width="2"/></g>')  # fmt: skip
        body.append(text(left + width + 14, y, label, 11, INK_2))
    return svg(left + width + 170, bottom + 28, body, f"Effect on resolution of {condition} vs. {baseline}")


SHIFT_MEASURES = [
    ("exploration_ratio", "Exploration share"), ("modification_ratio", "Modification share"),
    ("test_ratio", "Test share"), ("utility_ratio", "Utility share"), ("error_rate", "Error-turn rate"),
    ("productive_turn_ratio", "Productive-turn share"), ("first_modification_timing", "First edit (run position)"),
    ("P1_explore_before_modify", "P1 explore before edit"), ("P2_moderate_exploration", "P2 moderate exploration"),
    ("P4_fast_cascade_recovery", "P4 fast error recovery"), ("P5_short_trajectory", "P5 short run"),
    ("P6_low_late_entropy", "P6 low late entropy"), ("P7_test_after_modify", "P7 test after edit"),
]  # fmt: skip


def shift_svg(conditions: list[str], means: dict[str, dict[str, float | None]]) -> str:
    """Mean of each 0-1 process measure per condition on one shared 0-1 axis (shares and pattern rates)."""
    left, top, width, rh = 230, 104, 420, 30
    body = header("Process shift between conditions", "Mean over runs; shares of turns, run position, or share of runs showing the pattern")  # fmt: skip
    x = left
    for k, condition in enumerate(conditions):
        body.append(f'<circle cx="{x + 6}" cy="{top - 46}" r="5.5" fill="{SERIES[k]}"/>')
        body.append(text(x + 16, top - 46, condition, 11, INK_2))
        x += 40 + 7 * len(condition)
    bottom = top + len(SHIFT_MEASURES) * rh
    for k in range(5):
        gx = left + width * k / 4
        body.append(f'<line x1="{gx}" y1="{top - 10}" x2="{gx}" y2="{bottom}" stroke="{GRID}"/>')
        body.append(text(gx, bottom + 12, f"{k / 4:g}", 10, INK_2, "middle"))
    for i, (key, label) in enumerate(SHIFT_MEASURES):
        y = top + i * rh + rh / 2
        body.append(text(16, y, label, 12))
        values = [(c, means[c].get(key)) for c in conditions if means[c].get(key) is not None]
        if len(values) > 1:
            xs = [left + width * v for _, v in values]
            body.append(f'<line x1="{min(xs)}" y1="{y}" x2="{max(xs)}" y2="{y}" stroke="{GRID}" stroke-width="3"/>')
        for c, v in values:
            k = conditions.index(c)
            dy = (k - (len(conditions) - 1) / 2) * 8  # equal values stay visible
            body.append(f'<g><title>{escape(f"{label}, {c}: {v:.2f}")}</title><circle cx="{left + width * v}" cy="{y + dy}" '
                        f'r="5.5" fill="{SERIES[k]}" stroke="{SURFACE}" stroke-width="2"/></g>')  # fmt: skip
    return svg(left + width + 40, bottom + 28, body, "Process shift between conditions")
