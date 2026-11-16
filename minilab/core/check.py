"""Integrity check for a mini-lab run directory: is every trajectory complete, traceable and free of eval leakage?

Usage: python -m minilab.core.check runs/<name> [--subset SWE-bench-Live/SWE-bench-Live --split lite]
"""

import json
from pathlib import Path

import typer

from minilab.core.module import Add, Replace, apply_sections

app = typer.Typer(add_completion=False)
SECTION_KINDS = {"Add": Add, "Replace": Replace}


def leaks(instance: dict) -> list[str]:
    """Strings that must never appear in module outputs: test file paths, eval test ids, added lines of the gold patch."""
    ids = [instance.get(key) or [] for key in ("FAIL_TO_PASS", "PASS_TO_PASS")]
    tests = [t for v in ids for t in (json.loads(v) if isinstance(v, str) else v)]
    files = [line[6:] for line in instance.get("test_patch", "").splitlines() if line.startswith("+++ b/")]
    gold = [
        line[1:].strip()
        for line in instance.get("patch", "").splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    return files + tests + [line for line in gold if len(line) >= 30]


def module_outputs(traj: dict) -> list[str]:
    lab = traj["info"]["minilab"]
    texts = [json.dumps(a["value"]) for a in lab["artifacts"].values()]
    texts += [
        m["content"] if isinstance(m["content"], str) else json.dumps(m["content"])
        for m in traj["messages"]
        if m.get("extra", {}).get("minilab")
    ]
    for e in lab["events"]:
        texts += [s["text"] for s in e.get("sections", {}).values()]
        texts += [e["helper_call"]["answer"]] if "helper_call" in e else []
    return texts


def check_trajectory(traj: dict, template: str, instance: dict | None = None) -> list[str]:
    info, problems = traj["info"], []
    if missing := {"exit_status", "submission", "minilab", "config", "wall_time_seconds"} - set(info):
        return [f"missing info fields {sorted(missing)}"]
    lab, names = info["minilab"], {m["name"] for m in info["minilab"]["modules"]}
    sections = {
        name: SECTION_KINDS[s["kind"]](**{k: v for k, v in s.items() if k != "kind"})
        for e in lab["events"]
        for name, s in e.get("sections", {}).items()
    }
    if info["config"]["agent"]["instance_template"] != apply_sections(template, sections):
        problems.append("instance template differs from the config template plus the logged sections")
    if unknown := {e["producer"] for e in lab["events"]} - names:
        problems.append(f"events from unknown producers {sorted(unknown)}")
    if unknown := {m["extra"]["minilab"] for m in traj["messages"] if m.get("extra", {}).get("minilab")} - names:
        problems.append(f"injected messages from unknown modules {sorted(unknown)}")
    if unpriced := {e["producer"] for e in lab["events"] if "helper_call" in e} - set(lab["costs"]):
        problems.append(f"helper calls without recorded cost {sorted(unpriced)}")
    if instance is not None:
        outputs = "\n".join(module_outputs(traj))
        problems += [f"leak: {s!r} appears in module outputs" for s in leaks(instance) if s in outputs]
    return problems


def check_run(run_dir: Path, instances: list[dict] | None = None) -> dict[str, list[str]]:
    """Map each problem source (run or trajectory path) to its problems; empty dict means the run is clean."""
    problems = {
        str(run_dir): [f"missing {f}" for f in ("config.json", "provenance.json") if not (run_dir / f).exists()]
    }
    if problems[str(run_dir)]:
        return problems
    template = json.loads((run_dir / "config.json").read_text())["agent"]["instance_template"]
    by_id = {i["instance_id"]: i for i in instances or []}
    for path in sorted(run_dir.rglob("*.traj.json")):
        traj = json.loads(path.read_text())
        problems[str(path)] = check_trajectory(traj, template, by_id.get(traj.get("instance_id")))
    return {k: v for k, v in problems.items() if v}


@app.command()
def main(
    run_dir: Path,
    subset: str = typer.Option("", "--subset", help="Dataset to check for leakage of eval tests and the gold patch"),
    split: str = typer.Option("test", "--split", help="Dataset split"),
) -> None:
    instances = None
    if subset:
        from datasets import load_dataset

        from minisweagent.run.benchmarks.swebench import DATASET_MAPPING

        instances = list(load_dataset(DATASET_MAPPING.get(subset, subset), split=split))
    problems = check_run(run_dir, instances)
    for source, items in problems.items():
        print(f"{source}:\n" + "\n".join(f"  - {p}" for p in items))
    print("OK" if not problems else f"{len(problems)} file(s) with problems")
    raise typer.Exit(1 if problems else 0)


if __name__ == "__main__":
    app()
