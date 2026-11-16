"""Run mini-lab (mini-SWE-agent + research modules) on SWE-bench-style datasets in batch mode.

Usage (from the repository root):
    python -m minilab.core.runner -c swebench.yaml -c minilab/configs/swelive.yaml -c <experiment>.yaml \\
        --subset SWE-bench-Live/SWE-bench-Live --split lite --slice 0:10 -o runs/<name>
"""

import concurrent.futures
import json
import time
import traceback
from pathlib import Path

import typer
from rich.live import Live

from minilab.core.agent import LabAgent
from minilab.core.context import Context
from minilab.core.module import apply_sections, call, load_modules, overrides
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


class LabProgressAgent(LabAgent, ProgressTrackingAgent):
    pass


def check_config(config: dict) -> None:
    """Fail on unknown keys that mini would silently ignore."""
    if unknown := set(config.get("agent", {})) - set(AgentConfig.model_fields):
        raise ValueError(f"Unknown agent config keys: {sorted(unknown)}")
    if unknown := set(config.get("minilab", {})) - {"modules"}:
        raise ValueError(f"Unknown minilab config keys: {sorted(unknown)}")


def run_attempt(instance: dict, config: dict, traj_path: Path, progress_manager: RunBatchProgressManager) -> dict:
    """One agent run with the per-attempt hooks: before_run, setup_env, prompt_sections, (agent hooks), after_run."""
    modules = load_modules(config.get("minilab", {}).get("modules", {}))
    ctx = Context(task=instance["problem_statement"], instance=instance)
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
                ctx.log(module.name, sections={k: {"kind": type(v).__name__, "text": v.text} for k, v in added.items()})
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
        result = agent.run(ctx.task)
    except Exception as e:
        logger.error(f"Error processing instance {instance['instance_id']}: {e}", exc_info=True)
        result = {"exit_status": type(e).__name__, "submission": "", "exception_str": str(e)}
        result["traceback"] = traceback.format_exc()
    finally:
        ctx.hook, ctx.step = "after_run", agent.n_calls if agent else 0
        for m in modules:
            result = m.after_run(result, ctx)
        result["wall_time_seconds"] = round(time.time() - start, 2)
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
        modules, ctx = (
            load_modules(config.get("minilab", {}).get("modules", {})),
            Context(task=instance["problem_statement"], instance=instance),
        )
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
    shuffle: bool = typer.Option(False, "--shuffle", help="Shuffle instances"),
    output: str = typer.Option("", "-o", "--output", help="Output directory"),
    workers: int = typer.Option(1, "-w", "--workers", help="Number of worker threads"),
    attempts: int = typer.Option(1, "--attempts", help="Independent attempts per instance (best-of-N)"),
    model: str | None = typer.Option(None, "-m", "--model", help="Model to use"),
    redo_existing: bool = typer.Option(False, "--redo-existing", help="Redo existing instances"),
    config_spec: list[str] = typer.Option([str(DEFAULT_CONFIG_FILE)], "-c", "--config", help="Config files or key=value pairs, merged in order"),
) -> None:
    # fmt: on
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    add_file_handler(output_path / "minilab.log")
    config = recursive_merge(*[get_config_from_spec(spec) for spec in config_spec], {"model": {"model_name": model or UNSET}})
    check_config(config)
    load_modules(config.get("minilab", {}).get("modules", {}))
    (output_path / "config.json").write_text(json.dumps(config, indent=2))

    from datasets import load_dataset

    instances = filter_instances(
        list(load_dataset(DATASET_MAPPING.get(subset, subset), split=split)), filter_spec=filter_spec, slice_spec=slice_spec, shuffle=shuffle
    )
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
