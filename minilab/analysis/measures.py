"""Outcome, compute and process measures of one trajectory. Process measures are command-pattern heuristics."""

import re

EDIT = re.compile(
    r"sed -i|perl -[a-z]*i|\bgit apply\b|\bpatch -p|(cat|echo|printf|tee)\b[^|]*>\s*(?!/dev/null|/tmp/)\S+"
    r"|\btee\s+(?!-a\s+/tmp/|/tmp/)\S+|open\([^)]*['\"][wa]['\"]|\.write_text\("
)
TEST = re.compile(
    r"\b(pytest|py\.test|unittest|tox|nox|go test|cargo test|mvn test|gradle test|make test|ctest|jest|mocha|vitest)\b"
    r"|\b(npm|yarn|pnpm) (run )?test\b"
)
REPRO = re.compile(r"\brepro\w*\.\w+|\breproduce\w*")
PLAN = re.compile(r"\bplan\b|^\s*(1[.)]|- \[ \]|step 1\b)", re.I | re.M)


def steps(traj: dict) -> list[tuple[str, list[str]]]:
    """(assistant text, commands) for every model step."""
    return [
        (
            m.get("content") if isinstance(m.get("content"), str) else "",
            [a.get("command", "") for a in m["extra"]["actions"]],
        )
        for m in traj["messages"]
        if m.get("role") == "assistant" and "actions" in m.get("extra", {})
    ]


def patch_stats(patch: str) -> dict:
    lines = patch.splitlines()
    return {
        "files_touched": sum(line.startswith("diff --git") for line in lines),
        "lines_added": sum(line.startswith("+") and not line.startswith("+++") for line in lines),
        "lines_removed": sum(line.startswith("-") and not line.startswith("---") for line in lines),
    }


def measure(traj: dict) -> dict:
    info, lab = traj["info"], traj["info"].get("minilab", {})
    all_steps = steps(traj)
    commands = [c for _, cmds in all_steps for c in cmds]
    first_edit = next((i for i, (_, cmds) in enumerate(all_steps, 1) if any(EDIT.search(c) for c in cmds)), None)
    before_edit = all_steps[: (first_edit or len(all_steps) + 1) - 1]
    return {
        "exit_status": info.get("exit_status", ""),
        "submitted": bool(info.get("submission", "").strip()),
        "steps": info.get("model_stats", {}).get("api_calls", len(all_steps)),
        "agent_cost": info.get("model_stats", {}).get("instance_cost", 0.0),
        "helper_cost": sum(lab.get("costs", {}).values()),
        "helper_tokens": sum(lab.get("tokens", {}).values()),
        "wall_time_seconds": info.get("wall_time_seconds"),
        "steps_to_first_edit": first_edit,
        "plan_before_first_edit": any(PLAN.search(text) for text, _ in before_edit),
        "test_commands": sum(bool(TEST.search(c)) for c in commands),
        "repro_script": any(REPRO.search(c) for c in commands),
        "git_diff_before_submit": any("git diff" in c for c in commands),
        "rejections": sum("rejected_patch" in e for e in lab.get("events", [])),
        **patch_stats(info.get("submission", "")),
    }
