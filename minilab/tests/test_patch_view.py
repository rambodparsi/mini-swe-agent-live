import json
from html.parser import HTMLParser

from typer.testing import CliRunner

from minilab.analysis.patch_view import (
    Hunk,
    Line,
    Source,
    app,
    line_tags,
    parse_patch,
    repo_of,
    split_rows,
    task_page,
    write_pages,
)
from minilab.tests.test_analysis import make_run
from minilab.tests.test_compare import PATCH_A, PATCH_B, PATCH_C


def test_parse_patch_numbers_lines_and_counts_changes():
    (file,) = parse_patch(PATCH_A)
    assert (file.path, file.added, file.removed, [h.old_start for h in file.hunks]) == ("pkg/mod.py", 1, 1, [10])
    assert [(line.kind, line.text, line.old, line.new) for line in file.hunks[0].lines] == [
        (" ", "    x = 1", 10, 10),
        ("-", "    return x", 11, None),
        ("+", "    return x + 1", None, 11),
    ]
    assert [(f.path, f.added, f.removed) for f in parse_patch(PATCH_C)] == [
        ("pkg/mod.py", 2, 1),
        ("pkg/other.py", 1, 1),
    ]
    assert parse_patch("") == [] and parse_patch("the-patch\n") == []


def test_split_rows_pair_removals_with_additions():
    hunk = Hunk(
        "@@",
        1,
        [
            Line("-", "a", 1, None),
            Line("-", "b", 2, None),
            Line("+", "c", None, 1),
            Line(" ", "d", 3, 2),
            Line("+", "e", None, 3),
        ],
    )
    assert [(left and left.text, right and right.text) for left, right in split_rows(hunk)] == [
        ("a", "c"),
        ("b", None),
        ("d", "d"),
        (None, "e"),
    ]


def sources() -> list[Source]:
    return [
        Source("reference", PATCH_C, reference=True),
        Source("s1", PATCH_A, resolved=True, exit_status="Submitted", turns=5, cost=0.05),
        Source("s2", PATCH_B, resolved=True, exit_status="Submitted", turns=6, cost=0.06),
        Source("s3", PATCH_C, resolved=False, exit_status="Submitted", turns=9, cost=0.1,
               failures={"FAIL_TO_PASS": ["tests/test_mod.py::test_f"]}),
    ]  # fmt: skip


def test_line_tags_count_runs_and_mark_reference_lines():
    tags = line_tags(sources())
    assert tags["s1"][("pkg/mod.py", "-", "return x")] == "all 3 runs · = ref"
    assert tags["s1"][("pkg/mod.py", "+", "return x + 1")] == "2 of 3 runs"
    assert tags["s3"][("pkg/other.py", "+", "a = 2")] == "only this run · = ref"
    assert tags["reference"][("pkg/mod.py", "+", "y = x + 1")] == "in 1 of 3 runs"


def test_task_page_links_base_commit_and_explains_outcomes():
    instance = {"repo": "owner/pkg", "problem_statement": "f() is <wrong>", "FAIL_TO_PASS": '["tests/test_mod.py::test_f"]',
                "PASS_TO_PASS": ["a", "b"], "test_patch": PATCH_A.replace("pkg/mod.py", "tests/test_mod.py")}  # fmt: skip
    page = task_page("owner__pkg-7", "b0__abc", "0123456789abcdef", sources(), instance)
    HTMLParser().feed(page)
    assert 'href="https://github.com/owner/pkg/tree/0123456789abcdef"' in page
    assert 'href="https://github.com/owner/pkg/blob/0123456789abcdef/pkg/other.py#L1"' in page
    assert "f() is &lt;wrong&gt;" in page and "identical to s1" in page and "identical to reference" in page
    assert (
        "Tests that fail before the fix and must pass after it (1)" in page
        and "2 other tests must keep passing" in page
    )
    assert "<td>s3</td><td>FAIL_TO_PASS</td><td><code>tests/test_mod.py::test_f</code></td>" in page
    assert "Evaluation test changes" in page and "tests/test_mod.py" in page
    assert page.count('class="file compact"') == 6 and "s1 vs s2</h3><p class='note'>Same changed lines (2)" in page
    assert repo_of("owner__pkg-7", {}) == "owner/pkg"


def test_write_pages_for_runs_with_and_without_reference(tmp_path):
    run = tmp_path / "runs" / "b0__abc"
    for seed in ("s1", "s2"):
        make_run(tmp_path, run / seed, False, ["repo__x-1"] if seed == "s1" else [])
    for seed in ("s1", "s2"):
        report = run / seed / "eval" / "repo__x-2" / "report.json"
        report.parent.mkdir(parents=True)
        report.write_text(json.dumps({"resolved": False, "FAIL_TO_PASS": {"success": [], "failure": ["t::f"]}}))
    instances = {"repo__x-1": {"repo": "repo/x", "patch": PATCH_A, "base_commit": "abc"}}
    tasks = write_pages(run, tmp_path / "a", instances)
    assert [(task, [s.name for s in sources]) for task, _, sources in tasks] == [
        ("repo__x-1", ["reference", "s1", "s2"]),
        ("repo__x-2", ["s1", "s2"]),
    ]
    assert sorted(p.name for p in (tmp_path / "a").iterdir()) == ["index.html", "repo__x-1.html", "repo__x-2.html"]
    page = (tmp_path / "a" / "repo__x-2.html").read_text()
    assert "No reference patch" in page and "<td>s2</td><td>FAIL_TO_PASS</td>" in page
    result = CliRunner().invoke(app, [str(run), "-o", str(tmp_path / "b")])
    assert result.exit_code == 0 and "2 task pages (0 with the reference patch)" in result.output
    write_pages(run, tmp_path / "c", instances)
    assert all(
        (tmp_path / "a" / f).read_bytes() == (tmp_path / "c" / f).read_bytes() for f in ("index.html", "repo__x-1.html")
    )
