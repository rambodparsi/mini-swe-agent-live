import json
from dataclasses import dataclass

import pytest

from minilab import Add, Module
from minilab.core.runner import process_instance
from minilab.tests.test_core import SUBMIT, text_outputs
from minisweagent.config import get_config_from_spec
from minisweagent.run.benchmarks.utils.batch_progress import RunBatchProgressManager
from minisweagent.utils.serialize import recursive_merge


@dataclass
class Lab(Module):
    name = "lab"
    category = "requirements"

    def before_run(self, ctx):
        ctx.put("srs", f"SRS for: {ctx.task}", self.name)

    def prompt_sections(self, ctx):
        return {"Requirements": Add(ctx.get("srs"))}

    def after_run(self, result, ctx):
        return {**result, "srs_used": ctx.get("srs")}

    def select_attempt(self, attempts, ctx):
        return attempts[-1]


@pytest.mark.parametrize(("attempts", "traj_dir", "chosen"), [(1, "", None), (2, "attempt_0", 1)])
def test_process_instance_runs_hooks_and_saves(tmp_path, attempts, traj_dir, chosen):
    config = recursive_merge(
        get_config_from_spec("swebench.yaml"),
        {
            "environment": {"environment_class": "local", "cwd": str(tmp_path)},
            "model": {
                "model_class": "minisweagent.models.test_models.DeterministicModel",
                "outputs": text_outputs(["echo hi"], [SUBMIT]),
            },
            "minilab": {"modules": {"minilab.tests.test_runner.Lab": {}}},
        },
    )
    out = tmp_path / "out"
    process_instance(
        {"instance_id": "repo__x-1", "problem_statement": "Fix it"},
        out,
        config,
        RunBatchProgressManager(1, tmp_path / "exit.yaml"),
        attempts=attempts,
    )
    assert json.loads((out / "preds.json").read_text())["repo__x-1"]["model_patch"] == "the-patch\n"
    traj = json.loads((out / "repo__x-1" / traj_dir / "repo__x-1.traj.json").read_text())
    assert (traj["info"]["exit_status"], traj["info"]["srs_used"]) == ("Submitted", "SRS for: Fix it")
    assert traj["info"]["wall_time_seconds"] >= 0
    assert "## Requirements\nSRS for: Fix it\n\n</instructions>" in traj["messages"][1]["content"]
    srs = traj["info"]["minilab"]["artifacts"]["srs"]
    assert (srs["producer"], srs["hook"], srs["version"]) == ("lab", "before_run", 1)
    selection = out / "repo__x-1" / "selection.json"
    assert (json.loads(selection.read_text())["chosen"] if selection.exists() else None) == chosen
