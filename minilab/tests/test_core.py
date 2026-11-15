import json
from dataclasses import dataclass

import pytest
import yaml

from minilab import Add, LabAgent, Module, Replace, apply_sections, check_modules, load_modules
from minilab.core.runner import check_config
from minisweagent.agents.default import DefaultAgent
from minisweagent.config import builtin_config_dir
from minisweagent.environments.local import LocalEnvironment
from minisweagent.models.test_models import (
    DeterministicModel,
    DeterministicToolcallModel,
    make_output,
    make_toolcall_output,
)

SUBMIT = "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && echo the-patch"
SWEBENCH = yaml.safe_load((builtin_config_dir / "benchmarks" / "swebench.yaml").read_text())


def text_outputs(*steps: list[str]) -> list[dict]:
    return [make_output(f"step {i}", [{"command": c} for c in cmds]) for i, cmds in enumerate(steps)]


def toolcall_outputs(*steps: list[str]) -> list[dict]:
    outputs = []
    for i, cmds in enumerate(steps):
        actions = [{"command": c, "tool_call_id": f"call_{i}_{j}"} for j, c in enumerate(cmds)]
        calls = [
            {"id": a["tool_call_id"], "type": "function", "function": {"name": "bash", "arguments": json.dumps(a)}}
            for a in actions
        ]
        outputs.append(make_toolcall_output(None, calls, actions))
    return outputs


MODELS = {"text": (DeterministicModel, text_outputs), "toolcall": (DeterministicToolcallModel, toolcall_outputs)}


def run(agent_class, kind: str, steps: list[list[str]], tmp_path, **kwargs):
    model_class, make = MODELS[kind]
    agent = agent_class(
        model_class(outputs=make(*steps)),
        LocalEnvironment(cwd=str(tmp_path)),
        system_template="system",
        instance_template="{{task}}",
        **kwargs,
    )
    return agent.run("fix it"), agent


def strip(messages: list[dict]) -> list[dict]:
    return [{**m, "extra": {k: v for k, v in m.get("extra", {}).items() if k != "timestamp"}} for m in messages]


@dataclass
class RejectN(Module):
    times: int = 1
    name = "reject_n"
    category = "review"

    def on_submit(self, patch, ctx):
        if self.times:
            self.times -= 1
            return f"rejected: {patch}"
        return None


@dataclass
class Recorder(Module):
    name = "recorder"
    category = "planning"

    def before_query(self, agent, ctx):
        ctx.put("seen_step", ctx.step, self.name)
        return [{"role": "user", "content": "plan first"}] if ctx.step == 0 else []

    def on_execute(self, action, output, ctx):
        ctx.log(self.name, command=action["command"], returncode=output["returncode"])

    def transform_output(self, action, output, ctx):
        return {**output, "output": output["output"].upper()}


@pytest.mark.parametrize(
    ("kind", "steps", "step_limit", "exit_status"),
    [
        ("text", [["echo hi"], [SUBMIT]], 0, "Submitted"),
        ("toolcall", [["echo a", "echo b"], [SUBMIT]], 0, "Submitted"),
        ("text", [["ls /nonexistent-minilab-dir"], [SUBMIT]], 0, "Submitted"),
        ("toolcall", [["echo a"], ["echo b"], ["echo c"]], 2, "LimitsExceeded"),
    ],
)
def test_no_modules_equals_plain_mini(tmp_path, kind, steps, step_limit, exit_status):
    mini_info, mini = run(DefaultAgent, kind, steps, tmp_path, step_limit=step_limit)
    lab_info, lab = run(LabAgent, kind, steps, tmp_path, step_limit=step_limit)
    assert lab_info == mini_info
    assert lab_info["exit_status"] == exit_status
    assert strip(lab.messages) == strip(mini.messages)
    assert (lab.n_calls, lab.cost) == (mini.n_calls, mini.cost)
    assert lab.ctx.events == []


def test_rejection_keeps_tool_call_ids_and_continues(tmp_path):
    info, agent = run(LabAgent, "toolcall", [["echo a", SUBMIT, "echo c"], [SUBMIT]], tmp_path, modules=[RejectN()])
    assert (info["exit_status"], info["submission"]) == ("Submitted", "the-patch\n")
    tool = {m["tool_call_id"]: m["content"] for m in agent.messages if m.get("role") == "tool"}
    assert list(tool) == ["call_0_0", "call_0_1", "call_0_2"]
    assert "rejected: the-patch" in tool["call_0_1"] and "Submission rejected" in tool["call_0_1"]
    assert "action was not executed" in tool["call_0_2"]
    assert [(e["hook"], e["step"], e["rejected_patch"]) for e in agent.ctx.events] == [("on_submit", 1, "the-patch\n")]


@pytest.mark.parametrize(("times", "exit_status", "n_rejections"), [(0, "Submitted", 0), (99, "LimitsExceeded", 3)])
def test_rejection_never_ends_the_run(tmp_path, times, exit_status, n_rejections):
    info, agent = run(LabAgent, "text", [[SUBMIT]] * 4, tmp_path, step_limit=3, modules=[RejectN(times=times)])
    assert info["exit_status"] == exit_status
    assert len(agent.ctx.events) == n_rejections


def test_hooks_order_provenance_and_logging(tmp_path):
    info, agent = run(LabAgent, "text", [["echo hi"], [SUBMIT]], tmp_path, modules=[Recorder()])
    assert info["exit_status"] == "Submitted"
    assert [m["content"] for m in agent.messages[:4]] == ["system", "fix it", "plan first", "step 0"]
    assert "HI" in agent.messages[4]["content"]
    seen = agent.ctx.artifacts["seen_step"]
    assert (seen.value, seen.version, seen.producer, seen.hook, seen.step) == (1, 2, "recorder", "before_query", 1)
    on_execute, transform = agent.ctx.events
    assert (on_execute["hook"], on_execute["step"], on_execute["command"]) == ("on_execute", 1, "echo hi")
    assert transform["hook"] == "transform_output"
    assert (transform["raw_output"]["output"], transform["transformed_output"]["output"]) == ("hi\n", "HI\n")
    assert agent.serialize()["info"]["minilab"]["modules"] == [{"name": "recorder"}]


def test_prompt_sections_change_only_named_sections():
    template = SWEBENCH["agent"]["instance_template"]
    assert apply_sections(template, {}) == template
    new = apply_sections(
        template, {"Submission": Replace("Submit, then wait for review."), "Requirements": Add("Follow the SRS.")}
    )
    assert new.startswith(template.split("## Submission")[0])
    assert new.endswith(
        "## Submission\nSubmit, then wait for review.\n\n## Requirements\nFollow the SRS.\n\n</instructions>\n"
    )
    assert "You CANNOT continue working" in template and "You CANNOT continue working" not in new
    with pytest.raises(KeyError):
        apply_sections(template, {"No such section": Replace("x")})


def test_module_loading_and_checks():
    assert [
        m.name
        for m in load_modules({"minilab.tests.test_core.RejectN": {"times": 2}, "minilab.tests.test_core.Recorder": {}})
    ] == [
        "recorder",
        "reject_n",
    ]
    with pytest.raises(TypeError):
        load_modules({"minilab.tests.test_core.RejectN": {"tims": 2}})
    with pytest.raises(KeyError):
        load_modules({"srs": {}})
    with pytest.raises(ValueError):
        check_modules([RejectN(), RejectN()])
    check_config(SWEBENCH)
    with pytest.raises(ValueError):
        check_config({**SWEBENCH, "agent": {**SWEBENCH["agent"], "max_iterations": 50}})
    with pytest.raises(ValueError):
        check_config({"minilab": {"modules": {}, "modlues": {}}})
