"""GitHub-style pages to read and compare the patches of repeated runs, next to the reference (gold) patch.

One page per task: base commit and repository links, the issue, a summary of every run, each patch as a diff
(unified or split), all patches side by side per file, changed lines only in one of two patches, the evaluation
tests and which of them each run failed. Static, self-contained HTML; the same runs always give the same pages.
The reference patch and the evaluation tests come from the dataset (`--subset`); they are shown for analysis only.

Usage: python -m minilab.analysis.patch_view runs/<model>/<condition> --subset data/SWE-bench-Live --split lite \
           -o runs/analysis/patches
"""

import json
import re
from dataclasses import dataclass, field
from html import escape
from itertools import combinations, zip_longest
from pathlib import Path

import typer

from minilab.analysis.behavior import trajectory_paths
from minilab.analysis.compare import changed_lines, normalize_patch
from minilab.analysis.report import resolved_ids, run_dirs

app = typer.Typer(add_completion=False)


@dataclass
class Line:
    kind: str  # " " context, "+" added, "-" removed
    text: str
    old: int | None
    new: int | None


@dataclass
class Hunk:
    header: str
    old_start: int
    lines: list[Line] = field(default_factory=list)


@dataclass
class FileDiff:
    path: str
    hunks: list[Hunk] = field(default_factory=list)

    @property
    def added(self) -> int:
        return sum(line.kind == "+" for hunk in self.hunks for line in hunk.lines)

    @property
    def removed(self) -> int:
        return sum(line.kind == "-" for hunk in self.hunks for line in hunk.lines)


@dataclass
class Source:
    """One patch on the page: a run, or the reference patch."""

    name: str
    patch: str
    reference: bool = False
    resolved: bool | None = None
    exit_status: str = ""
    turns: int | None = None
    cost: float | None = None
    failures: dict[str, list[str]] = field(default_factory=dict)

    @property
    def files(self) -> list[FileDiff]:
        return parse_patch(self.patch)


def parse_patch(patch: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    old = new = 0
    for raw in patch.splitlines():
        if raw.startswith("diff --git "):
            files.append(FileDiff(raw.split(" b/", 1)[-1]))
        elif m := re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw):
            old, new = int(m.group(1)), int(m.group(2))
            files[-1].hunks.append(Hunk(raw, old))
        elif files and files[-1].hunks and raw[:1] in (" ", "+", "-", "") and not raw.startswith(("+++", "---")):
            kind = raw[:1] or " "
            files[-1].hunks[-1].lines.append(
                Line(kind, raw[1:], old if kind != "+" else None, new if kind != "-" else None)
            )
            old += kind != "+"
            new += kind != "-"
    return files


def split_rows(hunk: Hunk) -> list[tuple[Line | None, Line | None]]:
    """Rows of a split view: context on both sides; a block of removals faces the block of additions after it."""
    rows: list[tuple[Line | None, Line | None]] = []
    removed: list[Line] = []
    added: list[Line] = []

    def flush() -> None:
        rows.extend(zip_longest(removed, added))
        removed.clear()
        added.clear()

    for line in hunk.lines:
        if line.kind == "-":
            if added:
                flush()
            removed.append(line)
        elif line.kind == "+":
            added.append(line)
        else:
            flush()
            rows.append((line, line))
    flush()
    return rows


def repo_of(instance_id: str, instance: dict) -> str:
    return instance.get("repo") or instance_id.rsplit("-", 1)[0].replace("__", "/")


def test_ids(value) -> list[str]:
    return json.loads(value) if isinstance(value, str) else list(value or [])


CSS = """
:root { --fg:#1f2328; --muted:#59636e; --border:#d1d9e0; --bg:#ffffff; --soft:#f6f8fa;
  --add:#dafbe1; --add-num:#aceebb; --del:#ffebe9; --del-num:#ffcecb; --hunk:#ddf4ff; --link:#0969da;
  --ok:#1a7f37; --bad:#cf222e; }
* { box-sizing: border-box; }
body { margin: 0; font: 14px/1.5 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: var(--fg); background: var(--bg); }
main { max-width: 1400px; margin: 0 auto; padding: 24px 32px 64px; }
a { color: var(--link); text-decoration: none; } a:hover { text-decoration: underline; }
h1 { font-size: 24px; margin: 0 0 4px; } h2 { font-size: 20px; margin: 40px 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
h3 { font-size: 16px; margin: 24px 0 8px; }
.meta { color: var(--muted); display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 8px; }
code, pre, .code { font: 12px/1.6 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
pre.issue { white-space: pre-wrap; background: var(--soft); border: 1px solid var(--border); border-radius: 6px; padding: 12px 16px; max-height: 480px; overflow: auto; }
table.summary { border-collapse: collapse; width: 100%; }
table.summary th, table.summary td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; vertical-align: top; }
table.summary th { background: var(--soft); }
.badge { display: inline-block; padding: 0 8px; border-radius: 12px; font-size: 12px; font-weight: 600; border: 1px solid; white-space: nowrap; }
.badge.ok { color: var(--ok); border-color: var(--ok); } .badge.bad { color: var(--bad); border-color: var(--bad); }
.badge.ref { color: #8250df; border-color: #8250df; } .badge.na { color: var(--muted); border-color: var(--border); }
.toolbar { position: sticky; top: 0; background: var(--bg); padding: 8px 0; z-index: 2; display: flex; gap: 8px; align-items: center; border-bottom: 1px solid var(--border); }
.toolbar button { font: inherit; padding: 4px 12px; border: 1px solid var(--border); background: var(--soft); border-radius: 6px; cursor: pointer; }
.toolbar button.on { background: #1f2328; color: #fff; border-color: #1f2328; }
.file { border: 1px solid var(--border); border-radius: 6px; margin: 12px 0; overflow: hidden; }
.file-head { background: var(--soft); padding: 8px 12px; border-bottom: 1px solid var(--border); display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.file-head .path { font-weight: 600; } .plus { color: var(--ok); } .minus { color: var(--bad); }
table.diff { border-collapse: collapse; width: 100%; table-layout: fixed; }
table.diff td { padding: 0 8px; vertical-align: top; white-space: pre-wrap; word-break: break-all; }
td.num { width: 52px; color: var(--muted); text-align: right; user-select: none; }
td.sign { width: 18px; color: var(--muted); user-select: none; }
td.tag { width: 120px; color: var(--muted); font-size: 11px; white-space: nowrap; }
tr.add td { background: var(--add); } tr.add td.num { background: var(--add-num); }
tr.del td { background: var(--del); } tr.del td.num { background: var(--del-num); }
tr.hunk td { background: var(--hunk); color: var(--muted); }
td.add { background: var(--add); } td.del { background: var(--del); } td.add.num { background: var(--add-num); } td.del.num { background: var(--del-num); }
td.empty { background: var(--soft); }
body.split .unified { display: none; } body:not(.split) .split { display: none; }
.columns { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(620px, 1fr)); }
.file.compact { overflow-x: auto; }
.file.compact table.diff { table-layout: auto; min-width: 100%; width: max-content; }
.file.compact td.code { white-space: pre; word-break: normal; }
.file.compact tr.hunk td { white-space: nowrap; }
.columns .col h4 { margin: 0 0 6px; font-size: 13px; }
.unchanged { color: var(--muted); font-style: italic; padding: 8px 12px; border: 1px dashed var(--border); border-radius: 6px; }
.note { color: var(--muted); margin: 4px 0 8px; }
ul.lines { list-style: none; padding: 0; margin: 4px 0 12px; }
ul.lines li { font: 12px/1.6 ui-monospace, Menlo, Consolas, monospace; padding: 0 8px; white-space: pre-wrap; word-break: break-all; }
ul.lines li.add { background: var(--add); } ul.lines li.del { background: var(--del); }
details > summary { cursor: pointer; font-weight: 600; margin: 8px 0; }
"""

TOGGLE = """<script>
function view(mode){document.body.classList.toggle('split', mode==='split');
document.querySelectorAll('.toolbar button').forEach(function(b){b.classList.toggle('on', b.dataset.mode===mode);});}
</script>"""


def outcome_badge(source: Source) -> str:
    if source.reference:
        return '<span class="badge ref">reference fix</span>'
    if source.resolved is None:
        return '<span class="badge na">not evaluated</span>'
    return (
        '<span class="badge ok">resolved</span>' if source.resolved else '<span class="badge bad">not resolved</span>'
    )


def line_tags(sources: list[Source]) -> dict[str, dict[tuple[str, str, str], str]]:
    """Per source, a short tag for each changed line: how many runs wrote it, and whether the reference has it."""
    runs = [s for s in sources if not s.reference]
    reference = next((changed_lines(s.patch) for s in sources if s.reference), None)
    counts: dict[tuple[str, str, str], int] = {}
    for s in runs:
        for key in changed_lines(s.patch):
            counts[key] = counts.get(key, 0) + 1
    tags = {}
    for s in sources:
        own = {}
        for key in changed_lines(s.patch):
            n = counts.get(key, 0)
            if s.reference:
                own[key] = f"in {n} of {len(runs)} runs"
            else:
                share = (
                    f"all {len(runs)} runs"
                    if n == len(runs)
                    else "only this run"
                    if n == 1
                    else f"{n} of {len(runs)} runs"
                )
                own[key] = share + (" · = ref" if reference is not None and key in reference else "")
        tags[s.name] = own
    return tags


def diff_tables(
    file: FileDiff, tags: dict[tuple[str, str, str], str], repo: str, commit: str, compact: bool = False
) -> str:
    unified, split = [], []
    for hunk in file.hunks:
        unified.append(
            f'<tr class="hunk"><td class="num"></td><td class="num"></td><td class="sign"></td><td>{escape(hunk.header)}</td><td class="tag"></td></tr>'
        )
        split.append(f'<tr class="hunk"><td class="num"></td><td colspan="3">{escape(hunk.header)}</td></tr>')
        for line in hunk.lines:
            cls = {"+": "add", "-": "del"}.get(line.kind, "")
            tag = tags.get((file.path, line.kind, line.text.strip()), "") if line.kind != " " else ""
            unified.append(
                f'<tr class="{cls}"><td class="num">{line.old or ""}</td><td class="num">{line.new or ""}</td>'
                f'<td class="sign">{escape(line.kind)}</td><td class="code">{escape(line.text)}</td><td class="tag">{escape(tag)}</td></tr>'
            )
        for left, right in split_rows(hunk):
            cells = []
            for side, line in (("old", left), ("new", right)):
                if line is None:
                    cells.append('<td class="num empty"></td><td class="code empty"></td>')
                    continue
                cls = (
                    "del" if side == "old" and line.kind == "-" else "add" if side == "new" and line.kind == "+" else ""
                )
                number = line.old if side == "old" else line.new
                cells.append(
                    f'<td class="num {cls}">{number or ""}</td><td class="code {cls}">{escape(line.text)}</td>'
                )
            split.append(f"<tr>{''.join(cells)}</tr>")
    if compact:  # side-by-side columns: no tag column, unbroken code lines that scroll
        unified = [re.sub(r'<td class="tag">.*?</td>', "", row) for row in unified]
    first = file.hunks[0].old_start if file.hunks else 1
    link = f"https://github.com/{repo}/blob/{commit}/{file.path}#L{first}"
    tag_col = "" if compact else '<col style="width:120px">'
    return (
        f'<div class="file{" compact" if compact else ""}"><div class="file-head"><span class="path">{escape(file.path)}</span>'
        f'<span class="plus">+{file.added}</span><span class="minus">−{file.removed}</span>'
        f'<a href="{escape(link)}">view file at base commit</a></div>'
        f'<table class="diff unified"><colgroup><col style="width:52px"><col style="width:52px"><col style="width:18px"><col>{tag_col}</colgroup>{"".join(unified)}</table>'
        f'<table class="diff split"><colgroup><col style="width:52px"><col><col style="width:52px"><col></colgroup>{"".join(split)}</table></div>'
    )


def summary_table(sources: list[Source]) -> str:
    rows, seen = [], {}
    for s in sources:
        key = tuple(normalize_patch(s.patch))
        same = seen.get(key, "")
        seen.setdefault(key, s.name)
        files = s.files
        failed = sum(len(v) for v in s.failures.values())
        failed_text = "" if s.reference or s.resolved is None else f"{failed} evaluation test(s)" if failed else "none"
        rows.append(
            f"<tr><td><b>{escape(s.name)}</b></td><td>{outcome_badge(s)}</td><td>{escape(s.exit_status)}</td>"
            f"<td>{'' if s.turns is None else s.turns}</td><td>{'' if s.cost is None else f'${s.cost:.3f}'}</td>"
            f"<td>{len(files)}</td><td><span class='plus'>+{sum(f.added for f in files)}</span> "
            f"<span class='minus'>−{sum(f.removed for f in files)}</span></td>"
            f"<td>{escape(f'identical to {same}') if same else ''}</td><td>{escape(failed_text)}</td></tr>"
        )
    head = "<tr><th>Patch</th><th>Outcome</th><th>Exit</th><th>Turns</th><th>Cost</th><th>Files</th><th>Lines</th><th>Same patch as</th><th>Failed tests</th></tr>"  # noqa: E501
    return f'<table class="summary">{head}{"".join(rows)}</table>'


def patches_section(sources: list[Source], repo: str, commit: str) -> str:
    tags, out, seen = line_tags(sources), [], {}
    for s in sources:
        key = tuple(normalize_patch(s.patch))
        body = (
            "".join(diff_tables(f, tags[s.name], repo, commit) for f in s.files)
            or '<p class="unchanged">Empty patch.</p>'
        )
        if key in seen:
            out.append(
                f"<details><summary>{escape(s.name)} {outcome_badge(s)}: identical to {escape(seen[key])} (show)</summary>{body}</details>"
            )
        else:
            seen[key] = s.name
            out.append(f"<h3>{escape(s.name)} {outcome_badge(s)}</h3>{body}")
    return "".join(out)


def by_file_section(sources: list[Source], repo: str, commit: str) -> str:
    tags = line_tags(sources)
    paths = list(dict.fromkeys(f.path for s in sources for f in s.files))
    out = []
    for path in paths:
        columns = []
        for s in sources:
            file = next((f for f in s.files if f.path == path), None)
            body = (
                diff_tables(file, tags[s.name], repo, commit, compact=True)
                if file
                else '<p class="unchanged">File not changed.</p>'
            )
            columns.append(f'<div class="col"><h4>{escape(s.name)} {outcome_badge(s)}</h4>{body}</div>')
        out.append(f'<h3><code>{escape(path)}</code></h3><div class="columns">{"".join(columns)}</div>')
    return "".join(out)


def differences_section(sources: list[Source]) -> str:
    def items(lines: set) -> str:
        if not lines:
            return '<p class="note">none</p>'
        rows = "".join(
            f'<li class="{"add" if sign == "+" else "del"}">{escape(f"{path}  {sign} {text}")}</li>'
            for path, sign, text in sorted(lines)
        )
        return f'<ul class="lines">{rows}</ul>'

    out = []
    for a, b in combinations(sources, 2):
        la, lb = changed_lines(a.patch), changed_lines(b.patch)
        if la == lb:
            out.append(
                f"<h3>{escape(a.name)} vs {escape(b.name)}</h3><p class='note'>Same changed lines ({len(la)}).</p>"
            )
            continue
        out.append(
            f"<h3>{escape(a.name)} vs {escape(b.name)}</h3><p class='note'>{len(la & lb)} changed line(s) in both; "
            f"{len(la - lb)} only in {escape(a.name)}; {len(lb - la)} only in {escape(b.name)}.</p>"
            f"<p><b>Only in {escape(a.name)}</b></p>{items(la - lb)}<p><b>Only in {escape(b.name)}</b></p>{items(lb - la)}"
        )
    return "".join(out)


def tests_section(sources: list[Source], instance: dict, repo: str, commit: str) -> str:
    runs = [s for s in sources if not s.reference]
    out = []
    for group, label in (
        ("FAIL_TO_PASS", "fail before the fix and must pass after it"),
        ("PASS_TO_PASS", "must keep passing"),
    ):
        expected = test_ids(instance.get(group))
        if group == "FAIL_TO_PASS" and expected:
            out.append(
                f"<h3>Tests that {label} ({len(expected)})</h3><ul class='lines'>"
                + "".join(f"<li>{escape(t)}</li>" for t in expected)
                + "</ul>"
            )
        elif group == "PASS_TO_PASS" and expected:
            out.append(f"<p class='note'>{len(expected)} other tests {label}.</p>")
    rows = []
    for s in runs:
        for group, failed in sorted(s.failures.items()):
            rows += [
                f"<tr><td>{escape(s.name)}</td><td>{escape(group)}</td><td><code>{escape(t)}</code></td></tr>"
                for t in failed
            ]
    if rows:
        out.append(
            "<h3>Failed evaluation tests per run</h3><table class='summary'><tr><th>Run</th><th>Group</th><th>Test</th></tr>"
            + "".join(rows)
            + "</table>"
        )
    elif any(s.resolved is not None for s in runs):
        out.append("<p class='note'>No run failed an evaluation test.</p>")
    if instance.get("test_patch"):
        tables = "".join(diff_tables(f, {}, repo, commit) for f in parse_patch(instance["test_patch"]))
        out.append(
            f"<details><summary>Evaluation test changes (test patch, applied only for evaluation)</summary>{tables}</details>"
        )
    return "".join(out) or "<p class='note'>No evaluation information (run with --subset for the dataset's tests).</p>"


def task_page(instance_id: str, condition: str, base_commit: str, sources: list[Source], instance: dict) -> str:
    repo = repo_of(instance_id, instance)
    commit_link = f"https://github.com/{repo}/tree/{base_commit}"
    issue = instance.get("problem_statement", "")
    reference_note = (
        ""
        if any(s.reference for s in sources)
        else "<p class='note'>No reference patch: run with --subset to add the dataset's fix.</p>"
    )  # noqa: E501
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{escape(instance_id)} · patches</title>
<style>{CSS}</style>{TOGGLE}</head>
<body><main>
<p><a href="index.html">← all tasks</a></p>
<h1>{escape(instance_id)}</h1>
<div class="meta"><span>Repository: <a href="https://github.com/{escape(repo)}">{escape(repo)}</a></span>
<span>Base commit: <a href="{escape(commit_link)}" title="{escape(base_commit)}"><code>{escape(base_commit[:12])}</code></a></span>
<span>Condition: <code>{escape(condition)}</code></span>{f"<span>Created: {escape(str(instance['created_at']))}</span>" if instance.get("created_at") else ""}</div>
{f"<details><summary>Issue</summary><pre class='issue'>{escape(issue)}</pre></details>" if issue else ""}
<h2>Summary</h2>{summary_table(sources)}{reference_note}
<div class="toolbar"><span>Diff view:</span><button class="on" data-mode="unified" onclick="view('unified')">Unified</button>
<button data-mode="split" onclick="view('split')">Split</button>
<span class="note">Tags: how many runs wrote a changed line; “= ref” when the reference fix has the same line.</span></div>
<h2>Patches</h2>{patches_section(sources, repo, base_commit)}
<h2>Side by side, per file</h2>{by_file_section(sources, repo, base_commit)}
<h2>Changed lines that differ</h2>{differences_section(sources)}
<h2>Evaluation</h2>{tests_section(sources, instance, repo, base_commit)}
</main></body></html>
"""


def index_page(
    condition_names: list[str], tasks: list[tuple[str, str, list[Source]]], instances: dict[str, dict]
) -> str:
    rows = []
    for instance_id, base_commit, sources in tasks:
        repo = repo_of(instance_id, instances.get(instance_id, {}))
        runs = " ".join(f"{escape(s.name)} {outcome_badge(s)}" for s in sources if not s.reference)
        distinct = len({tuple(normalize_patch(s.patch)) for s in sources if not s.reference})
        rows.append(
            f'<tr><td><a href="{escape(instance_id)}.html">{escape(instance_id)}</a></td><td>{escape(repo)}</td>'
            f'<td><a href="https://github.com/{escape(repo)}/tree/{escape(base_commit)}"><code>{escape(base_commit[:12])}</code></a></td>'
            f"<td>{runs}</td><td>{distinct}</td><td>{'yes' if any(s.reference for s in sources) else 'no'}</td></tr>"
        )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Patches · {escape(", ".join(condition_names))}</title><style>{CSS}</style></head>
<body><main><h1>Patches of repeated runs</h1>
<p class="meta">Condition: {escape(", ".join(condition_names))} · {len(tasks)} tasks</p>
<table class="summary"><tr><th>Task</th><th>Repository</th><th>Base commit</th><th>Runs</th><th>Distinct patches</th><th>Reference fix</th></tr>
{"".join(rows)}</table></main></body></html>
"""


def failures_of(run_dir: Path, instance_id: str) -> tuple[bool | None, dict[str, list[str]]]:
    report = run_dir / "eval" / instance_id / "report.json"
    if not report.exists():
        resolved = resolved_ids(run_dir)
        return (None if resolved is None else instance_id in resolved), {}
    data = json.loads(report.read_text())
    failures = {
        g: data.get(g, {}).get("failure", [])
        for g in ("FAIL_TO_PASS", "PASS_TO_PASS")
        if data.get(g, {}).get("failure")
    }
    return bool(data.get("resolved")), failures


def collect_tasks(condition_dir: Path, instances: dict[str, dict]) -> list[tuple[str, str, list[Source]]]:
    by_task: dict[str, tuple[str, list[Source]]] = {}
    for run_dir in run_dirs(condition_dir):
        for path in trajectory_paths(run_dir):
            traj = json.loads(path.read_text())
            info, instance_id = traj["info"], traj["instance_id"]
            resolved, failures = failures_of(run_dir, instance_id)
            source = Source(run_dir.name, info.get("submission", ""), False, resolved, info.get("exit_status", ""),
                            info.get("model_stats", {}).get("api_calls"), info.get("model_stats", {}).get("instance_cost"), failures)  # fmt: skip
            commit = info.get("base_commit") or instances.get(instance_id, {}).get("base_commit", "")
            by_task.setdefault(instance_id, (commit, []))[1].append(source)
    tasks = []
    for instance_id in sorted(by_task):
        commit, runs = by_task[instance_id]
        gold = instances.get(instance_id, {}).get("patch")
        tasks.append(
            (
                instance_id,
                commit,
                ([Source("reference", gold, reference=True)] if gold else []) + sorted(runs, key=lambda s: s.name),
            )
        )
    return tasks


def write_pages(condition_dir: Path, output: Path, instances: dict[str, dict]) -> list[tuple[str, str, list[Source]]]:
    tasks = collect_tasks(condition_dir, instances)
    output.mkdir(parents=True, exist_ok=True)
    for instance_id, commit, sources in tasks:
        page = task_page(instance_id, condition_dir.name, commit, sources, instances.get(instance_id, {}))
        (output / f"{instance_id}.html").write_text(page)
    (output / "index.html").write_text(index_page([condition_dir.name], tasks, instances))
    return tasks


@app.command()
def main(
    condition_dir: Path = typer.Argument(..., help="Condition folder (seed runs inside) or one run folder"),
    subset: str = typer.Option("", "--subset", help="Dataset for the reference patch and evaluation tests"),
    split: str = typer.Option("test", "--split", help="Dataset split"),
    output: Path = typer.Option(Path("runs/analysis/patches"), "-o", "--output", help="Folder for the pages"),
) -> None:
    instances: dict[str, dict] = {}
    if subset:
        from datasets import load_dataset

        from minisweagent.run.benchmarks.swebench import DATASET_MAPPING

        instances = {i["instance_id"]: dict(i) for i in load_dataset(DATASET_MAPPING.get(subset, subset), split=split)}
    tasks = write_pages(condition_dir, output, instances)
    with_reference = sum(any(s.reference for s in sources) for _, _, sources in tasks)
    print(
        f"{len(tasks)} task pages ({with_reference} with the reference patch) in {output}; open {output / 'index.html'}"
    )


if __name__ == "__main__":
    app()
