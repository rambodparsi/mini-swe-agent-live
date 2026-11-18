import csv
import json
import math

import pytest
from typer.testing import CliRunner

from minilab.analysis.actions import classify_command, error_type, split_command, turn_category
from minilab.analysis.behavior import Turn, app, cfg_features, patterns, phase_transition, table2_features
from minilab.tests.test_analysis import make_run
from minilab.tests.test_core import SUBMIT, text_outputs

EDIT_BODY = "from pathlib import Path\np = Path('pkg/mod.py')\np.write_text(p.read_text().replace('a && b', 'c'))"
EDIT = f"python - <<'PY'\n{EDIT_BODY}\nPY"
CHECK = "python - <<'PY'\nimport pkg\nassert pkg.f() == 1; print('ok')\nPY"


def test_split_command_keeps_quotes_heredocs_and_redirections():
    assert split_command("cd /testbed && grep -n 'a && b; c' x.py 2>&1 | head -5; ls") == [
        "cd /testbed",
        "grep -n 'a && b; c' x.py 2>&1",
        "head -5",
        "ls",
    ]
    assert split_command('echo "$(git diff | wc -l)" && pwd') == ['echo "$(git diff | wc -l)"', "pwd"]
    parts = classify_command(f"cd /testbed && python - <<'PY' && git diff > patch.txt\n{EDIT_BODY}\nPY")
    assert [(p.program, p.category, p.rule) for p in parts] == [
        ("cd", "Navigation", "navigation"),
        ("python", "Modification", "python_edit"),
        ("git", "Utility", "make_patch"),
    ]


@pytest.mark.parametrize(
    ("command", "category", "rule"),
    [
        ("sed -n '1,80p' pkg/mod.py", "Exploration", "sed_print"),
        ("rg -n 'def f' pkg", "Exploration", "read_search"),
        ("xargs -0 grep -l foo", "Exploration", "read_search"),
        ("sed -i 's/a/b/' pkg/mod.py", "Modification", "in_place_edit"),
        ("sed -i 's/a/b/' /tmp/check.py", "Test", "scratch_script"),
        ("cat > pkg/new.py <<'EOF'\nx = 1\nEOF", "Modification", "redirect_write"),
        ("cat > /tmp/repro.py <<'EOF'\nprint(1)\nEOF", "Test", "scratch_script"),
        ("echo 'x' >> README.md", "Modification", "redirect_write"),
        ("git apply fix.diff", "Modification", "git_apply"),
        ("rm pkg/old.py", "Modification", "file_change"),
        ("rm -f /tmp/repro.py", "Utility", "scratch_cleanup"),
        (EDIT, "Modification", "python_edit"),
        (CHECK, "Test", "python_run"),
        (
            "python - <<'PY'\nfrom pathlib import Path\ns = Path('pkg/form.html').read_text()\nPath('/tmp/f.js').write_text(s)\nPY",
            "Test",
            "python_scratch",
        ),
        (
            "python - <<'PY'\np = 'pkg/mod.py'\ns = open(p).read().replace('a', 'b')\nopen(p, 'w').write(s)\nPY",
            "Modification",
            "python_edit",
        ),
        ("python -c 'import pkg; print(pkg.__file__)'", "Test", "python_run"),
        ("PYTHONPATH=Lib python -m pytest -q tests/test_x.py", "Test", "test_runner"),
        ("timeout 60 pytest -x", "Test", "test_runner"),
        ("bin/test sympy/printing", "Test", "test_runner"),
        ("venv/bin/ruff check pkg", "Test", "lint"),
        ("bash -c 'pytest -q'", "Test", "shell_c"),
        ("node /tmp/check.js", "Test", "script_run"),
        ("node --version", "Utility", "version_or_help"),
        ("git status --short", "Utility", "git"),
        ("git diff > patch.txt", "Utility", "make_patch"),
        ("pip install -q quickjs", "Utility", "pip"),
        ("echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT", "Utility", "submit"),
        ("pwd", "Navigation", "navigation"),
        ("fi", "Utility", "shell_syntax"),
        ("frobnicate --all", "Unknown", "unknown"),
    ],
)
def test_classify(command, category, rule):
    assert [(p.category, p.rule) for p in classify_command(command)] == [(category, rule)]


@pytest.mark.parametrize(
    ("command", "category"),
    [
        ("cd /testbed && pwd", "Navigation"),
        ("cd /testbed && git status && sed -n '1,9p' x.py", "Exploration"),
        (f"cat x.py && python -m pytest -q; python - <<'PY'\n{EDIT_BODY}\nPY", "Modification"),
        ("grep -n f x.py && python -m pytest -q", "Test"),
        ("echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt", "Utility"),
        ("cd /testbed && frobnicate", "Unknown"),
    ],
)
def test_turn_category_priority(command, category):
    assert turn_category(classify_command(command)) == category


@pytest.mark.parametrize(
    ("command", "output", "returncode", "exception", "expected"),
    [
        ("ls", "x.py\n", 0, "", ""),
        ("rg foo .", "bash: line 1: rg: command not found\n", 127, "", "command_not_found"),
        ("rg foo . | head", "bash: line 1: rg: command not found\n", 0, "", "command_not_found"),
        ("grep -n nothing x.py", "", 1, "", ""),
        ("grep -n f x.py && python t.py", "Traceback (most recent call last):\nValueError: bad\n", 1, "", "traceback"),
        ("python -m pytest", "....F\n1 failed, 4 passed in 0.1s\n", 1, "", "test_failure"),
        ("python t.py", "  File 't.py'\nSyntaxError: invalid syntax\n", 1, "", "syntax_error"),
        ("python t.py", "ModuleNotFoundError: No module named 'x'\n", 1, "", "import_error"),
        ("cat a.py && false", "try:\n    import x\nexcept ImportError:\n" + "line\n" * 30, 1, "", "nonzero_exit"),
        ("sleep 100", "", -9, "Command timed out", "timeout"),
        ("echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT", "", None, "", ""),
    ],
)
def test_error_type(command, output, returncode, exception, expected):
    assert error_type(output, returncode, exception, classify_command(command)) == expected


def turns(categories: str, errors: str = "", commands: list[str] | None = None) -> list[Turn]:
    names = {"E": "Exploration", "M": "Modification", "T": "Test", "N": "Navigation", "U": "Utility"}
    return [
        Turn(i + 1, (commands or [f"c{i}" for i in range(len(categories))])[i], [], names[c],
             1 if errors[i : i + 1] == "x" else 0, "nonzero_exit" if errors[i : i + 1] == "x" else "", 0, 0, 0, 0.0)
        for i, c in enumerate(categories)
    ]  # fmt: skip


def test_table2_features_by_hand():
    f = table2_features(turns("EEMTEU", ".xx...", ["a", "b", "c", "d", "a", "e"]))
    assert (f["exploration_ratio"], f["modification_ratio"], f["test_ratio"], f["navigation_ratio"]) == (
        0.5,
        1 / 6,
        1 / 6,
        0.0,
    )
    assert f["transition_entropy"] == pytest.approx(math.log2(5))
    assert (f["exploration_frontloading"], f["first_modification_timing"], f["phase_transition_point"]) == (
        2 / 3,
        1 / 3,
        None,
    )
    assert (f["late_stage_entropy"], f["error_rate"], f["cascade_rate"], f["recovery_rate"]) == (0.0, 1 / 3, 0.5, 1.0)
    assert (f["repetition_rate"], f["mean_cascade_length"], f["max_cascade_length"]) == (1 / 6, 2, 2)
    assert f["productive_turn_ratio"] == 0.5
    clean = table2_features(turns("EEMT"))
    assert (clean["cascade_rate"], clean["recovery_rate"], clean["first_cascade_length"]) == (None, None, None)


@pytest.mark.parametrize(
    ("categories", "expected"), [(["E", "M", "M"], 2 / 3), (["E", "M", "E"], None), (["M", "E", "E", "E"], 0.5)]
)
def test_phase_transition(categories, expected):
    assert phase_transition(categories) == expected


def test_cfg_features_by_hand():
    assert cfg_features(turns("EMT", "x..")) == {
        "motif_entropy": 1.0,
        "cfg_transition_entropy": 0.0,
        "self_loop_rate": 0.0,
        "revisit_rate": 0.0,
        "backtrack_rate": 0.0,
        "post_error_motif_ratio": 1.0,
    }
    loop = cfg_features(turns("EEEEEEEEE"))
    assert (loop["self_loop_rate"], loop["revisit_rate"], loop["backtrack_rate"]) == (3 / 7, 3 / 8, 0.0)
    oscillate = cfg_features(turns("EMEMEMEMEMEM"))
    assert (oscillate["self_loop_rate"], oscillate["revisit_rate"], oscillate["backtrack_rate"]) == (0.0, 3 / 11, 1 / 3)


def test_patterns():
    row = table2_features(turns("EMTE", "x..."))
    cats = ["Exploration", "Modification", "Test", "Exploration"]
    medians = {"max_cascade_length": 2, "trajectory_length": 5, "late_stage_entropy": 0.5}
    assert patterns(row, cats, medians) == {
        "P1_explore_before_modify": True,
        "P2_moderate_exploration": True,
        "P3_short_cascades": True,
        "P4_fast_cascade_recovery": True,
        "P5_short_trajectory": True,
        "P6_low_late_entropy": True,
        "P7_test_after_modify": True,
    }
    assert patterns(table2_features(turns("TTT")), ["Test"] * 3, medians)["P1_explore_before_modify"] is None


def test_behavior_cli_on_runs_is_complete_and_deterministic(tmp_path):
    steps = [["grep -n foo missing.py"], ["sed -i 's/a/b/' x.py"], ["python -m pytest -q"], ["git diff"], [SUBMIT]]
    run = tmp_path / "runs" / "b0__abc"
    for s in ("s1", "s2"):
        make_run(tmp_path, run / s, False, ["repo__x-1"] if s == "s1" else [])
    for path in run.rglob("*.traj.json"):
        traj = json.loads(path.read_text())
        traj["messages"][2:] = []
        for i, step in enumerate(text_outputs(*steps)):
            traj["messages"] += [step, {"role": "tool", "content": "", "extra": {"returncode": int(i == 0) * 2,
                                 "raw_output": "grep: missing.py: No such file or directory" if i == 0 else ""}}]  # fmt: skip
        path.write_text(json.dumps(traj))
    outs = [tmp_path / "a", tmp_path / "b"]
    for out in outs:
        assert CliRunner().invoke(app, [str(run), "-o", str(out)]).exit_code == 0
    files = sorted(p.relative_to(outs[0]) for p in outs[0].rglob("*") if p.is_file())
    assert all((outs[0] / f).read_bytes() == (outs[1] / f).read_bytes() for f in files)
    assert len([f for f in files if f.parts[1] == "action_timelines"]) == 4
    rows = list(csv.DictReader((outs[0] / "level1" / "run_features.csv").open()))
    first = next(r for r in rows if r["seed"] == "s1" and r["instance_id"] == "repo__x-1")
    assert (first["resolved"], first["timeline"], first["errors_file_not_found"]) == ("True", "E! M T U U", "1")
    assert (first["P7_test_after_modify"], first["P1_explore_before_modify"]) == ("True", "True")
    pairs = list(csv.DictReader((outs[0] / "level2" / "pairwise_similarity.csv").open()))
    assert [(p["instance_id"], p["run_a"], p["run_b"], p["same_outcome"]) for p in pairs] == [
        ("repo__x-1", "s1", "s2", "False"),
        ("repo__x-2", "s1", "s2", "True"),
    ]
    assert {f.name for f in (outs[0] / "summary" / "figures").iterdir()} >= {
        "b0__abc__timelines.svg",
        "b0__abc__similarity.svg",
    }
    assert len(list((outs[0] / "level2" / "issue_comparisons").iterdir())) == 2
    audit = list(csv.DictReader((outs[0] / "level1" / "classification_audit.csv").open()))
    assert {a["rule"] for a in audit} >= {"read_search", "in_place_edit", "test_runner", "git", "submit"}
