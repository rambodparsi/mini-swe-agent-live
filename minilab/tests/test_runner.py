import json
from dataclasses import dataclass

import pytest

from minilab import Add, Module
from minilab.core.check import check_run
from minilab.core.helper_llm import ask
from minilab.core.runner import (
    check_resume,
    experiment_name,
    log_run,
    next_run_dir,
    process_instance,
    write_run_files,
)
from minilab.tests.test_core import SUBMIT, text_outputs
from minisweagent.config import get_config_from_spec
from minisweagent.models.test_models import make_output
from minisweagent.run.benchmarks.utils.batch_progress import RunBatchProgressManager
from minisweagent.utils.serialize import recursive_merge


@dataclass
class Lab(Module):
    name = "lab"
    category = "requirements"

    def before_run(self, ctx):
        ctx.put("srs", ask(ctx, self.name, f"Write an SRS for: {ctx.task}"), self.name)

    def setup_env(self, env, ctx):
        env.execute({"command": "echo spec > srs.txt"})
        return {"files": ["srs.txt"]}

    def prompt_sections(self, ctx):
        return {"Requirements": Add(ctx.get("srs"))}

    def after_run(self, result, ctx):
        return {**result, "srs_used": ctx.get("srs")}

    def select_attempt(self, attempts, ctx):
        return attempts[-1]


def lab_config(tmp_path, srs: str = "SRS for: Fix it"):
    return recursive_merge(
        get_config_from_spec("swebench.yaml"),
        {
            "environment": {"environment_class": "local", "cwd": str(tmp_path)},
            "model": {
                "model_class": "minisweagent.models.test_models.DeterministicModel",
                "outputs": text_outputs(["echo hi"], [SUBMIT]),
            },
            "minilab": {
                "modules": {"minilab.tests.test_runner.Lab": {}},
                "helper_model": {
                    "model_class": "minisweagent.models.test_models.DeterministicModel",
                    "model_name": "deterministic",
                    "outputs": [make_output(srs, [], cost=0.5)],
                },
            },
        },
    )


@pytest.mark.parametrize(("attempts", "traj_dir", "chosen"), [(1, "", None), (2, "attempt_0", 1)])
def test_process_instance_runs_hooks_and_saves(tmp_path, attempts, traj_dir, chosen):
    config = lab_config(tmp_path)
    out = tmp_path / "out"
    process_instance(
        {"instance_id": "repo__x-1", "problem_statement": "Fix it", "base_commit": "abc"},
        out,
        config,
        RunBatchProgressManager(1, tmp_path / "exit.yaml"),
        attempts=attempts,
    )
    assert json.loads((out / "preds.json").read_text())["repo__x-1"]["model_patch"] == "the-patch\n"
    traj = json.loads((out / "repo__x-1" / traj_dir / "repo__x-1.traj.json").read_text())
    assert (traj["info"]["exit_status"], traj["info"]["srs_used"]) == ("Submitted", "SRS for: Fix it")
    assert traj["info"]["wall_time_seconds"] >= 0 and traj["info"]["base_commit"] == "abc"
    assert traj["info"]["minilab"]["costs"] == {"lab": 0.5}
    assert "## Requirements\nSRS for: Fix it\n\n</instructions>" in traj["messages"][1]["content"]
    srs = traj["info"]["minilab"]["artifacts"]["srs"]
    assert (srs["producer"], srs["hook"], srs["version"]) == ("lab", "before_run", 1)
    assert [(e["producer"], e["hook"]) for e in traj["info"]["minilab"]["events"]] == [
        ("lab", "before_run"),
        ("lab", "setup_env"),
        ("lab", "prompt_sections"),
    ]
    helper, setup, sections = traj["info"]["minilab"]["events"]
    assert helper["helper_call"]["prompt"] == "Write an SRS for: Fix it"
    assert setup["report"] == {"files": ["srs.txt"]} and (tmp_path / "srs.txt").read_text() == "spec\n"
    assert sections["sections"] == {"Requirements": {"kind": "Add", "text": "SRS for: Fix it", "before": None}}
    selection = out / "repo__x-1" / "selection.json"
    assert (json.loads(selection.read_text())["chosen"] if selection.exists() else None) == chosen


def tamper_template(traj: dict) -> None:
    traj["info"]["config"]["agent"]["instance_template"] += "extra"


def tamper_producer(traj: dict) -> None:
    traj["info"]["minilab"]["events"][0]["producer"] = "ghost"


def tamper_cost(traj: dict) -> None:
    traj["info"]["minilab"]["costs"] = {}


@pytest.mark.parametrize(
    ("tamper", "instance", "problem"),
    [
        (None, {}, None),
        (None, {"FAIL_TO_PASS": '["test_x"]'}, "leak: 'test_x'"),
        (None, {"test_patch": "+++ b/tests/test_x.py\n"}, "leak: 'tests/test_x.py'"),
        (None, {"patch": "+    return parse(text) or default_config()\n"}, "leak: 'return parse"),
        (tamper_template, {}, "instance template differs"),
        (tamper_producer, {}, "events from unknown producers ['ghost']"),
        (tamper_cost, {}, "helper calls without recorded cost ['lab']"),
    ],
)
def test_check_run_finds_problems(tmp_path, tamper, instance, problem):
    srs = "Edit tests/test_x.py so that `return parse(text) or default_config()` holds."
    config, out = lab_config(tmp_path, srs), tmp_path / "out"
    instance = {"instance_id": "repo__x-1", "problem_statement": "Fix it", **instance}
    process_instance(instance, out, config, RunBatchProgressManager(1, tmp_path / "exit.yaml"))
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "REVISION").write_text("abc123\n")
    write_run_files(out, config, str(tmp_path / "data"), "lite")
    traj_path = out / "repo__x-1" / "repo__x-1.traj.json"
    if tamper:
        traj = json.loads(traj_path.read_text())
        tamper(traj)
        traj_path.write_text(json.dumps(traj))
    problems = check_run(out, [instance]).get(str(traj_path), [])
    assert (problems[0].startswith(problem) if problem else problems) == (True if problem else [])
    saved = json.loads((out / "provenance.json").read_text())
    assert (saved["modules"], saved["dataset_revision"], saved["split"]) == (
        ["minilab.tests.test_runner.Lab"],
        "abc123",
        "lite",
    )
    (out / "provenance.json").unlink()
    assert check_run(out) == {str(out): ["missing provenance.json"]}


def test_run_folders_never_reuse_and_separate_setups(tmp_path):
    config = {"model": {"model_name": "openai/gpt-5.1", "model_kwargs": {"reasoning_effort": "medium"}}}
    tasks = {"dataset": "d", "split": "lite", "instances": ["a", "b"]}
    first = next_run_dir(tmp_path, config, "b0", tasks)
    assert (first.parent.parent.name, first.parent.name.split("__")[0], first.name) == ("gpt-5.1", "b0", "s1")
    first.mkdir(parents=True)
    assert next_run_dir(tmp_path, config, "b0", tasks) == first.parent / "s2"
    changed = [
        next_run_dir(
            tmp_path, {"model": {**config["model"], "model_kwargs": {"reasoning_effort": "high"}}}, "b0", tasks
        ),
        next_run_dir(tmp_path, config, "b0", {**tasks, "instances": ["a"]}),
        next_run_dir(tmp_path, config, "p1", tasks),
    ]
    assert len({first.parent, *(p.parent for p in changed)}) == 4 and all(p.name == "s1" for p in changed)
    assert (
        next_run_dir(tmp_path, {"model": {"model_name": "anthropic/claude-x"}}, "b0", tasks).parent.parent.name
        == "claude-x"
    )


@pytest.mark.parametrize(
    ("specs", "name"),
    [
        (["swebench.yaml", "minilab/configs/swelive.yaml", "minilab/configs/experiments/b0.yaml"], "b0"),
        (["minilab/configs/experiments/b0.yaml", "minilab/configs/experiments/p1.yaml", "model.yaml"], "p1"),
        (["swebench.yaml", "agent.step_limit=10"], "custom"),
    ],
)
def test_experiment_name(specs, name):
    assert experiment_name(specs) == name


def test_resume_only_with_same_config_and_runs_are_indexed(tmp_path):
    config = {"model": {"model_name": "m"}, "minilab": {"modules": {"lab": {}}}}
    run = tmp_path / "runs" / "m" / "b0__abc" / "s1"
    check_resume(run, config)
    run.mkdir(parents=True)
    write_run_files(run, config)
    check_resume(run, config)
    with pytest.raises(ValueError):
        check_resume(run, {**config, "model": {"model_name": "other"}})
    for _ in range(2):
        log_run(tmp_path / "runs", run, config, "b0", 10)
    entries = [json.loads(line) for line in (tmp_path / "runs" / "index.jsonl").read_text().splitlines()]
    assert [(e["output"], e["model"], e["experiment"], e["modules"], e["tasks"]) for e in entries] == [
        (str(run), "m", "b0", ["lab"], 10)
    ] * 2
