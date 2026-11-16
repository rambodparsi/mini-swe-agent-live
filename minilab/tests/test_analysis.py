import csv
import json

import pytest
from typer.testing import CliRunner

from minilab.analysis.measures import measure
from minilab.analysis.report import app, mcnemar, paired
from minilab.core.runner import process_instance, select_instances
from minilab.scripts.make_pilot import pick
from minilab.tests.test_core import SUBMIT, text_outputs
from minilab.tests.test_runner import lab_config
from minisweagent.models.test_models import make_output
from minisweagent.run.benchmarks.utils.batch_progress import RunBatchProgressManager

PATCH = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@\n-old\n+new\n+more\n"


def test_measure_process_and_patch():
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "task"},
        make_output("Look around.", [{"command": "ls"}]),
        make_output("Plan:\n1. reproduce\n2. fix", [{"command": "cat > repro.py <<'EOF'\nprint(1)\nEOF"}]),
        make_output("Fix.", [{"command": "sed -i 's/old/new/' x.py"}, {"command": "python -m pytest tests"}]),
        make_output("Check.", [{"command": "git diff > patch.txt"}, {"command": "echo hi > /tmp/notes"}]),
    ]
    info = {"exit_status": "Submitted", "submission": PATCH, "model_stats": {"api_calls": 4, "instance_cost": 0.5}}
    info["minilab"] = {"costs": {"r": 0.25}, "tokens": {"r": 10}, "events": [{"rejected_patch": "p"}, {"x": 1}]}
    assert measure({"info": info, "messages": messages}) | {"wall_time_seconds": 0} == {
        "exit_status": "Submitted",
        "submitted": True,
        "steps": 4,
        "agent_cost": 0.5,
        "helper_cost": 0.25,
        "helper_tokens": 10,
        "wall_time_seconds": 0,
        "steps_to_first_edit": 2,
        "plan_before_first_edit": False,
        "test_commands": 1,
        "repro_script": True,
        "git_diff_before_submit": True,
        "rejections": 1,
        "files_touched": 1,
        "lines_added": 2,
        "lines_removed": 1,
    }
    planned = [*messages[:2], make_output("Plan:\n1. fix", [{"command": "ls"}]), *messages[4:]]
    assert measure({"info": info, "messages": planned})["plan_before_first_edit"] is True
    assert measure({"info": {}, "messages": messages[:3]})["steps_to_first_edit"] is None


def rows(condition: str, resolved: dict[str, list[bool]]) -> list[dict]:
    return [
        {"condition": condition, "seed": f"s{s}", "instance_id": task, "resolved": value, "steps": 1.0}
        for task, values in resolved.items()
        for s, value in enumerate(values)
    ]


def test_paired_comparison_averages_seeds_per_task():
    base = rows("b0", {"a": [True, True], "b": [False, False], "c": [False, True], "d": [True, True]})
    treat = rows("p1", {"a": [True, True], "b": [True, True], "c": [True, True], "d": [True, True], "e": [True, True]})
    result = paired(base, treat, "resolved", n_boot=2000)
    assert (result["tasks"], result["baseline"], result["treatment"], result["diff"]) == (4, 0.625, 1.0, 0.375)
    assert 0 <= result["ci95"][0] <= 0.375 <= result["ci95"][1] <= 1
    assert paired(base, rows("x", {"z": [True]}), "resolved") == {"metric": "resolved", "tasks": 0}


@pytest.mark.parametrize(
    ("base", "treat", "expected"),
    [
        ([True] * 3 + [False] * 7, [True] * 10, {"only_baseline": 0, "only_treatment": 7, "p": 2 / 2**7}),
        ([True, False], [False, True], {"only_baseline": 1, "only_treatment": 1, "p": 1.0}),
        ([True], [True], {"only_baseline": 0, "only_treatment": 0, "p": 1.0}),
    ],
)
def test_mcnemar(base, treat, expected):
    make = lambda name, values: rows(name, {f"t{i}": [v] for i, v in enumerate(values)})  # noqa: E731
    assert mcnemar(make("b0", base), make("p1", treat)) == expected


def make_run(tmp_path, run_dir, modules: bool, resolved: list[str] | None):
    config = lab_config(tmp_path)
    if not modules:
        config["minilab"]["modules"] = {}
    for instance_id in ["repo__x-1", "repo__x-2"]:
        config["model"]["outputs"] = text_outputs(["echo hi"], [SUBMIT])
        instance = {"instance_id": instance_id, "problem_statement": "Fix it"}
        process_instance(instance, run_dir, config, RunBatchProgressManager(1, tmp_path / "exit.yaml"))
    if resolved is not None:
        (run_dir / "eval").mkdir()
        (run_dir / "eval" / "results.json").write_text(json.dumps({"success_ids": resolved}))


def test_report_end_to_end(tmp_path):
    make_run(tmp_path, tmp_path / "runs" / "b0" / "s1", False, ["repo__x-1"])
    make_run(tmp_path, tmp_path / "runs" / "b0" / "s2", False, [])
    make_run(tmp_path, tmp_path / "runs" / "lab", True, ["repo__x-1", "repo__x-2"])
    out = tmp_path / "analysis"
    args = [str(tmp_path / "runs" / c) for c in ("b0", "lab")] + ["--baseline", "b0", "-o", str(out)]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    table = list(csv.DictReader((out / "tasks.csv").open()))
    assert [(r["condition"], r["seed"], r["instance_id"], r["resolved"]) for r in table] == [
        ("b0", "s1", "repo__x-1", "True"),
        ("b0", "s1", "repo__x-2", "False"),
        ("b0", "s2", "repo__x-1", "False"),
        ("b0", "s2", "repo__x-2", "False"),
        ("lab", "lab", "repo__x-1", "True"),
        ("lab", "lab", "repo__x-2", "True"),
    ]
    report = json.loads((out / "report.json").read_text())
    assert (report["summary"]["b0"]["runs"], report["summary"]["b0"]["resolved"]) == (2, 0.25)
    assert (report["summary"]["lab"]["helper_cost"], report["summary"]["lab"]["agent_cost"]) == (0.5, 2.0)
    resolved = report["comparisons"]["lab"]["resolved"]
    assert (resolved["tasks"], resolved["diff"]) == (2, 0.75)
    assert (
        report["comparisons"]["lab"]["total_cost"]["diff"] == 0.5
        and "mcnemar_resolved" not in report["comparisons"]["lab"]
    )
    assert CliRunner().invoke(app, args[:2] + ["--baseline", "nope", "-o", str(out)]).exit_code != 0


def test_instance_selection_and_pilot_pick():
    instances = [{"instance_id": f"{repo}__{i}", "repo": repo} for repo in "abc" for i in range(5)]
    assert [i["instance_id"] for i in select_instances(instances, ["b__1", "a__0"])] == ["b__1", "a__0"]
    with pytest.raises(ValueError):
        select_instances(instances, ["z__9"])
    chosen = pick(instances, 6, seed=0)
    assert chosen == pick(list(reversed(instances)), 6, seed=0) == sorted(chosen)
    assert sorted(i.split("__")[0] for i in chosen) == ["a", "a", "b", "b", "c", "c"]
    assert pick(instances, 6, seed=1) != chosen and len(pick(instances, 100, seed=0)) == 15


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_small_pilot_is_inside_larger_pilot(seed):
    instances = [{"instance_id": f"{repo}__{i}", "repo": repo} for repo in "abcdefg" for i in range(3 + ord(repo) % 5)]
    small, large = pick(instances, 10, seed), pick(instances, 30, seed)
    assert set(small) < set(large) and len(small) == 10 and len(large) == 30
    assert len({i.split("__")[0] for i in small}) == 7


@pytest.mark.parametrize(
    ("names", "exit_code"), [(["b0__a1b2c3", "lab__d4e5f6"], 0), (["b0__a1b2c3", "b0__ffffff"], 2), (["lab", "p1"], 2)]
)
def test_report_baseline_by_short_name(tmp_path, names, exit_code):
    for name in names:
        make_run(tmp_path, tmp_path / "runs" / name / "s1", name.startswith("lab"), ["repo__x-1"])
    args = [str(tmp_path / "runs" / n) for n in names] + ["--baseline", "b0", "-o", str(tmp_path / "out")]
    assert CliRunner().invoke(app, args).exit_code == exit_code
