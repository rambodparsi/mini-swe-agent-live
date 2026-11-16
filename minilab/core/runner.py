"""Run mini-lab (mini-SWE-agent + research modules) on SWE-bench-style datasets in batch mode.

Usage (from the repository root):
    python -m minilab.core.runner -c swebench.yaml -c minilab/configs/swelive.yaml -c <experiment>.yaml \\
        --subset SWE-bench-Live/SWE-bench-Live --split lite --slice 0:10 -o runs/<name>
"""

import concurrent.futures
import hashlib
import json
import platform
import subprocess
import time
import traceback
from pathlib import Path

import typer
from rich.live import Live

import minisweagent
from minilab.core.agent import LabAgent
from minilab.core.context import Context
from minilab.core.module import apply_sections, call, load_modules, overrides, section_values
from minisweagent.agents.default import AgentConfig
from minisweagent.config import get_config_from_spec
from minisweagent.models import get_model
from minisweagent.run.benchmarks.swebench import (
    DATASET_MAPPING,
    DEFAULT_CONFIG_FILE,
    filter_instances,
    get_sb_environment,
    remove_from_preds_file,
    update_preds_file,
)
from minisweagent.run.benchmarks.utils.batch_progress import RunBatchProgressManager
from minisweagent.run.benchmarks.utils.common import ProgressTrackingAgent
from minisweagent.utils.log import add_file_handler, logger
from minisweagent.utils.serialize import UNSET, recursive_merge

app = typer.Typer(rich_markup_mode="rich", add_completion=False)
RUNS = Path("runs")


class LabProgressAgent(LabAgent, ProgressTrackingAgent):
    pass


def check_config(config: dict) -> None:
    """Fail on unknown keys that mini would silently ignore."""
    if unknown := set(config.get("agent", {})) - set(AgentConfig.model_fields):
        raise ValueError(f"Unknown agent config keys: {sorted(unknown)}")
    if unknown := set(config.get("minilab", {})) - {"modules", "helper_model"}:
        raise ValueError(f"Unknown minilab config keys: {sorted(unknown)}")


def helper_model_config(config: dict) -> dict:
    """`minilab.helper_model`, or the main model's name and kwargs (without the main model's class)."""
    model = config.get("model", {})
    default = {"model_name": model.get("model_name", ""), "model_kwargs": model.get("model_kwargs", {})}
    return config.get("minilab", {}).get("helper_model") or default


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=Path(__file__).parent).stdout.strip()


def dataset_revision(dataset: str) -> str:
    """Version of the dataset: the REVISION file of a local copy (scripts/download_dataset.py), else the Hub commit."""
    if Path(dataset).exists():
        return (Path(dataset) / "REVISION").read_text().strip() if (Path(dataset) / "REVISION").exists() else "unknown"
    from huggingface_hub import HfApi

    return HfApi().dataset_info(dataset).sha


def provenance(config: dict, dataset: str = "", split: str = "") -> dict:
    return {
        "dataset": dataset,
        "split": split,
        "dataset_revision": dataset_revision(dataset) if dataset else "",
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain")),
        "mini_version": minisweagent.__version__,
        "python": platform.python_version(),
        "modules": sorted(config.get("minilab", {}).get("modules", {})),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def select_instances(instances: list[dict], ids: list[str]) -> list[dict]:
    by_id = {i["instance_id"]: i for i in instances}
    if missing := [i for i in ids if i not in by_id]:
        raise ValueError(f"Instances not in the dataset: {missing}")
    return [by_id[i] for i in ids]


def fingerprint(*parts) -> str:
    """Short id of everything that defines a condition: the merged config and the task selection."""
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:6]


def experiment_name(config_spec: list[str]) -> str:
    """Name of the last config file from configs/experiments/, else "custom"."""
    return next((Path(s).stem for s in reversed(config_spec) if Path(s).parent.name == "experiments"), "custom")


def next_run_dir(root: Path, config: dict, experiment: str, tasks: dict) -> Path:
    """runs/<model>/<experiment>__<fingerprint>/s<k>, with k one past the existing seeds: never an existing folder."""
    model = str(config.get("model", {}).get("model_name") or "model").split("/")[-1]
    condition = root / model / f"{experiment}__{fingerprint(config, tasks)}"
    seeds = [int(p.name[1:]) for p in condition.glob("s*") if p.name[1:].isdigit()]
    return condition / f"s{max(seeds, default=0) + 1}"


def check_resume(output_path: Path, config: dict) -> None:
    """Resuming a run folder is only allowed with the same config, so one folder never mixes two setups."""
    saved = output_path / "config.json"
    if saved.exists() and json.loads(saved.read_text()) != json.loads(json.dumps(config)):
        raise ValueError(f"{output_path} was run with a different config; leave out -o to get a new folder")


def log_run(root: Path, output_path: Path, config: dict, experiment: str, n_tasks: int) -> None:
    """One line per run in runs/index.jsonl, to see what each folder is."""
    root.mkdir(parents=True, exist_ok=True)
    entry = {
        "output": str(output_path),
        "model": config.get("model", {}).get("model_name"),
        "experiment": experiment,
        "modules": sorted(config.get("minilab", {}).get("modules", {})),
        "tasks": n_tasks,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git_commit": git("rev-parse", "--short", "HEAD"),
    }
    with (root / "index.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")


def write_run_files(output_path: Path, config: dict, dataset: str = "", split: str = "") -> None:
    (output_path / "config.json").write_text(json.dumps(config, indent=2))
    (output_path / "provenance.json").write_text(json.dumps(provenance(config, dataset, split), indent=2))


def run_attempt(instance: dict, config: dict, traj_path: Path, progress_manager: RunBatchProgressManager) -> dict:
    """One agent run with the per-attempt hooks: before_run, setup_env, prompt_sections, (agent hooks), after_run."""
    modules = load_modules(config.get("minilab", {}).get("modules", {}))
    ctx = Context(task=instance["problem_statement"], instance=instance, helper_model=helper_model_config(config))
    agent, result, start = None, {}, time.time()
    try:
        call(modules, ctx, "before_run")
        env = get_sb_environment(config, instance)
        for module, report in zip(modules, call(modules, ctx, "setup_env", env)):
            if overrides(module, "setup_env"):
                ctx.log(module.name, report=report)
        agent_config, sections = dict(config.get("agent", {})), {}
        for module, added in zip(modules, call(modules, ctx, "prompt_sections")):
            if added:
                ctx.log(module.name, sections={k: {"kind": type(v).__name__, **vars(v)} for k, v in added.items()})
            sections |= added
        if sections:
            agent_config["instance_template"] = apply_sections(agent_config["instance_template"], sections)
        agent = LabProgressAgent(
            get_model(config=dict(config.get("model", {}))),
            env,
            modules=modules,
            ctx=ctx,
            progress_manager=progress_manager,
            instance_id=instance["instance_id"],
            **agent_config,
        )
        result = agent.run(ctx.task, **({"minilab_sections": section_values(sections)} if sections else {}))
    except Exception as e:
        logger.error(f"Error processing instance {instance['instance_id']}: {e}", exc_info=True)
        result = {"exit_status": type(e).__name__, "submission": "", "exception_str": str(e)}
        result["traceback"] = traceback.format_exc()
    finally:
        ctx.hook, ctx.step = "after_run", agent.n_calls if agent else 0
        for m in modules:
            result = m.after_run(result, ctx)
        result["wall_time_seconds"] = round(time.time() - start, 2)
        result["base_commit"] = instance.get("base_commit", "")
        if agent is not None:
            agent.save(traj_path, {"info": result, "instance_id": instance["instance_id"]})
    return result


def process_instance(
    instance: dict, output_dir: Path, config: dict, progress_manager: RunBatchProgressManager, attempts: int = 1
) -> None:
    """Run `attempts` independent attempts; with more than one, `select_attempt` picks the submitted patch."""
    instance_id = instance["instance_id"]
    instance_dir = output_dir / instance_id
    remove_from_preds_file(output_dir / "preds.json", instance_id)
    progress_manager.on_instance_start(instance_id)
    runs = [
        run_attempt(
            instance,
            config,
            instance_dir / (f"attempt_{i}" if attempts > 1 else "") / f"{instance_id}.traj.json",
            progress_manager,
        )
        for i in range(attempts)
    ]
    chosen = runs[0]
    if attempts > 1:
        modules = load_modules(config.get("minilab", {}).get("modules", {}))
        ctx = Context(task=instance["problem_statement"], instance=instance, helper_model=helper_model_config(config))
        ctx.hook = "select_attempt"
        chosen = next((m.select_attempt(runs, ctx) for m in modules if overrides(m, "select_attempt")), runs[0])
        (instance_dir / "selection.json").write_text(
            json.dumps(
                {
                    "chosen": next(i for i, r in enumerate(runs) if r is chosen),
                    "exit_statuses": [r["exit_status"] for r in runs],
                    **ctx.serialize(),
                },
                indent=2,
            )
        )
    update_preds_file(
        output_dir / "preds.json", instance_id, config.get("model", {}).get("model_name", ""), chosen["submission"]
    )
    progress_manager.on_instance_end(instance_id, chosen["exit_status"])


# fmt: off
@app.command()
def main(
    subset: str = typer.Option("lite", "--subset", help="SWEBench subset to use or path to a dataset"),
    split: str = typer.Option("dev", "--split", help="Dataset split"),
    slice_spec: str = typer.Option("", "--slice", help="Slice specification (e.g., '0:5' for first 5 instances)"),
    filter_spec: str = typer.Option("", "--filter", help="Filter instance IDs by regex"),
    instances_file: Path | None = typer.Option(None, "--instances", help="File with instance IDs, one per line (e.g. minilab/configs/pilot_instances.txt)"),
    shuffle: bool = typer.Option(False, "--shuffle", help="Shuffle instances"),
    output: str = typer.Option("", "-o", "--output", help="Output directory (default: a new runs/<model>/<experiment>__<id>/s<k>); give an existing one to resume it"),
    workers: int = typer.Option(1, "-w", "--workers", help="Number of worker threads"),
    attempts: int = typer.Option(1, "--attempts", help="Independent attempts per instance (best-of-N)"),
    model: str | None = typer.Option(None, "-m", "--model", help="Model to use"),
    redo_existing: bool = typer.Option(False, "--redo-existing", help="Redo existing instances"),
    config_spec: list[str] = typer.Option([str(DEFAULT_CONFIG_FILE)], "-c", "--config", help="Config files or key=value pairs, merged in order"),
) -> None:
    # fmt: on
    config = recursive_merge(*[get_config_from_spec(spec) for spec in config_spec], {"model": {"model_name": model or UNSET}})
    check_config(config)
    load_modules(config.get("minilab", {}).get("modules", {}))

    from datasets import load_dataset

    dataset = DATASET_MAPPING.get(subset, subset)
    instances = filter_instances(
        list(load_dataset(dataset, split=split)), filter_spec=filter_spec, slice_spec=slice_spec, shuffle=shuffle
    )
    if instances_file:
        instances = select_instances(instances, instances_file.read_text().split())
    tasks = {"dataset": dataset, "split": split, "instances": [i["instance_id"] for i in instances]}
    output_path = Path(output) if output else next_run_dir(RUNS, config, experiment_name(config_spec), tasks)
    check_resume(output_path, config)
    output_path.mkdir(parents=True, exist_ok=True)
    add_file_handler(output_path / "minilab.log")
    write_run_files(output_path, config, dataset, split)
    log_run(RUNS, output_path, config, experiment_name(config_spec), len(instances))
    logger.info(f"Output: {output_path}")
    if not redo_existing and (output_path / "preds.json").exists():
        done = json.loads((output_path / "preds.json").read_text())
        instances = [i for i in instances if i["instance_id"] not in done]
    logger.info(f"Running on {len(instances)} instances...")
    progress_manager = RunBatchProgressManager(len(instances), output_path / f"exit_statuses_{time.time()}.yaml")
    with Live(progress_manager.render_group, refresh_per_second=4):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(process_instance, i, output_path, config, progress_manager, attempts): i["instance_id"] for i in instances}
            for future in concurrent.futures.as_completed(futures):
                if (e := future.exception()) is not None:
                    progress_manager.on_uncaught_exception(futures[future], e)


if __name__ == "__main__":
    app()
