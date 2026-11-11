"""Check a SWE-bench-Live split before a run: size, fields, Docker image names, and (optionally) that images exist."""

import subprocess
from pathlib import Path

import typer
import yaml
from datasets import load_dataset
from huggingface_hub import HfApi

from minisweagent.run.benchmarks.swebench import DEFAULT_IMAGE_NAME_TEMPLATE, get_swebench_docker_image_name

app = typer.Typer(add_completion=False)
CONFIG = Path(__file__).parents[1] / "configs" / "swelive.yaml"


@app.command()
def main(
    dataset: str = typer.Option("SWE-bench-Live/SWE-bench-Live", help="Hugging Face dataset name"),
    split: str = typer.Option("lite", help="Dataset split"),
    n: int = typer.Option(2, "-n", help="Number of instances (in dataset order, as with --slice 0:n) to show/check"),
    config: Path = typer.Option(CONFIG, "-c", "--config", help="Config with run.image_name_template"),
    ids_out: Path | None = typer.Option(None, help="Write the first n instance IDs to this file, one per line"),
    check_images: bool = typer.Option(False, help="Check with `docker manifest inspect` that the first n images exist"),
) -> None:
    rows = load_dataset(dataset, split=split)
    template = (yaml.safe_load(config.read_text()).get("run") or {}).get(
        "image_name_template", DEFAULT_IMAGE_NAME_TEMPLATE
    )
    with_image = sum(bool(r.get("image_name") or r.get("docker_image")) for r in rows)
    revision = "local" if Path(dataset).exists() else HfApi().dataset_info(dataset).sha
    print(f"Dataset: {dataset} [{split}] at revision {revision}")
    print(f"Instances: {len(rows)}; with own image field: {with_image}; using template: {len(rows) - with_image}")
    print(f"Fields: {', '.join(rows.column_names)}")
    print(f"Image template: {template}")
    first = rows.select(range(min(n, len(rows))))
    missing = []
    for row in first:
        image = get_swebench_docker_image_name(row, template)
        found = ""
        if check_images:
            ok = subprocess.run(["docker", "manifest", "inspect", image], capture_output=True).returncode == 0
            found = "  [found]" if ok else "  [NOT FOUND]"
            missing += [] if ok else [image]
        print(f"  {row['instance_id']}: {image}{found}")
    if ids_out:
        ids_out.parent.mkdir(parents=True, exist_ok=True)
        ids_out.write_text("".join(f"{r['instance_id']}\n" for r in first))
    if missing:
        raise SystemExit(f"{len(missing)} image(s) not found")


if __name__ == "__main__":
    app()
