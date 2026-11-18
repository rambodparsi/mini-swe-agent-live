"""Static SVG figures for the behavior analysis (no plotting dependency; deterministic output).

Colors are the validated reference palette: categorical slots 1-3 for Exploration, Modification and Test,
neutral grays for the rest, and the single-hue blue ramp for similarity. Every cell also carries its
letter or value, so no information is carried by color alone."""

from html import escape

SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e2e1dc"
FILL = {
    "Exploration": "#2a78d6", "Modification": "#eb6834", "Test": "#1baf7a",
    "Utility": "#c3c2b7", "Navigation": "#e2e1dc", "Unknown": "#8a8984",
}  # fmt: skip
LETTER = {"Exploration": "E", "Modification": "M", "Test": "T", "Navigation": "N", "Utility": "U", "Unknown": "?"}
RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
        "#184f95", "#104281", "#0d366b"]  # fmt: skip
FONT = 'font-family="system-ui, -apple-system, Segoe UI, sans-serif"'


def text(
    x: float, y: float, value: str, size: int = 12, fill: str = INK, anchor: str = "start", weight: int = 400
) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
        f'dominant-baseline="central">{escape(value)}</text>'
    )


def svg(width: float, height: float, body: list[str], title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'{FONT} role="img" aria-label="{escape(title)}">\n<rect width="100%" height="100%" fill="{SURFACE}"/>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def timelines_svg(condition: str, tasks: list[list[dict]], turns: dict[tuple[str, str], list]) -> str:
    """One row per run, one cell per turn, grouped by task; error turns are outlined and marked with '!'."""
    cell, gap, label_w, top = 24, 2, 260, 78
    longest = max((len(turns[(r["instance_id"], r["seed"])]) for runs in tasks for r in runs), default=1)
    body = [text(16, 20, f"Action timelines: {condition}", 15, weight=600),
            text(16, 40, "One row per run, one cell per turn; outlined cells with ! are error turns", 12, INK_2)]  # fmt: skip
    x = 16
    for category in ("Exploration", "Modification", "Test", "Utility", "Navigation", "Unknown"):
        body.append(f'<rect x="{x}" y="54" width="14" height="14" rx="3" fill="{FILL[category]}"/>')
        body.append(text(x + 19, 61, f"{LETTER[category]} {category}", 11, INK_2))
        x += 30 + 7 * len(category) + 10
    y = top
    for runs in tasks:
        y += 8
        body.append(text(16, y + 9, runs[0]["instance_id"], 12, weight=600))
        y += 22
        for r in runs:
            status = {True: "resolved", False: "not resolved", None: "not evaluated"}[r["resolved"]]
            body.append(text(28, y + cell / 2, f"{r['seed']}  {status}", 11, INK_2))
            for k, t in enumerate(turns[(r["instance_id"], r["seed"])]):
                cx = label_w + k * (cell + gap)
                outline = f' stroke="{INK}" stroke-width="2"' if t.error else ""
                tip = f"turn {t.index}: {t.category}" + (f", error: {t.error}" if t.error else "")
                body.append(f'<g><title>{escape(tip)}</title><rect x="{cx}" y="{y}" width="{cell}" height="{cell - 4}" '
                            f'rx="4" fill="{FILL[t.category]}"{outline}/>')  # fmt: skip
                body.append(text(cx + cell / 2, y + (cell - 4) / 2, LETTER[t.category] + ("!" if t.error else ""), 10, INK, "middle", 600) + "</g>")  # fmt: skip
            y += cell + 2
    return svg(label_w + longest * (cell + gap) + 16, y + 16, body, f"Action timelines for {condition}")


COLUMNS = [
    ("sequence_similarity", "sequence", "(edit)"), ("lcs_ratio", "sequence", "(LCS)"),
    ("transition_jaccard", "transitions", ""), ("explored_files_jaccard", "explored", "files"),
    ("modified_files_jaccard", "modified", "files"), ("patch_text_similarity", "patch", "text"),
    ("changed_lines_jaccard", "changed", "lines"), ("touched_lines_jaccard", "patch", "location"),
]  # fmt: skip


def similarity_svg(condition: str, issues: list[dict]) -> str:
    """Tasks x similarity measures (mean over run pairs, 0-1), single-hue ramp with the value printed in each cell."""
    cell_w, cell_h, label_w, top = 72, 26, 260, 92
    body = [text(16, 20, f"Similarity of repeated runs: {condition}", 15, weight=600),
            text(16, 40, "Mean over run pairs of each task; 1 = identical, 0 = nothing in common", 12, INK_2)]  # fmt: skip
    for c, (_, line1, line2) in enumerate(COLUMNS):
        cx = label_w + c * (cell_w + 2) + cell_w / 2
        body += [text(cx, top - 28, line1, 11, INK_2, "middle"), text(cx, top - 14, line2, 11, INK_2, "middle")]
    body.append(text(label_w + len(COLUMNS) * (cell_w + 2) + 40, top - 21, "resolved", 11, INK_2, "middle"))
    for r, issue in enumerate(issues):
        y = top + r * (cell_h + 2)
        body.append(text(16, y + cell_h / 2, issue["instance_id"], 12))
        for c, (key, line1, line2) in enumerate(COLUMNS):
            value = issue[f"mean_{key}"]
            step = round(value * (len(RAMP) - 1))
            x = label_w + c * (cell_w + 2)
            tip = escape(f"{issue['instance_id']}, {line1} {line2}: {value:.2f}")
            body.append(f'<g><title>{tip}</title>'
                        f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" rx="4" fill="{RAMP[step]}"/>')  # fmt: skip
            body.append(text(x + cell_w / 2, y + cell_h / 2, f"{value:.2f}", 11, SURFACE if step >= 7 else INK, "middle") + "</g>")  # fmt: skip
        body.append(text(label_w + len(COLUMNS) * (cell_w + 2) + 40, y + cell_h / 2, f"{issue['resolved_runs']}/{issue['runs']}", 12, INK, "middle"))  # fmt: skip
    width = label_w + len(COLUMNS) * (cell_w + 2) + 80
    return svg(width, top + len(issues) * (cell_h + 2) + 20, body, f"Similarity of repeated runs for {condition}")
