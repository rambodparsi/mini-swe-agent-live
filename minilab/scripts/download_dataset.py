"""Download a fixed version of the dataset once; every later step uses the local copy (--subset data/SWE-bench-Live).

python minilab/scripts/download_dataset.py            # → data/SWE-bench-Live (+ REVISION) and configs/dataset_revision.txt
"""

from pathlib import Path

import typer
from huggingface_hub import HfApi, snapshot_download

app = typer.Typer(add_completion=False)
RECORD = Path(__file__).parents[1] / "configs" / "dataset_revision.txt"


@app.command()
def main(
    dataset: str = typer.Option("SWE-bench-Live/SWE-bench-Live", help="Hugging Face dataset name"),
    output: Path = typer.Option(
        Path("data/SWE-bench-Live"), "-o", "--output", help="Local folder (not version-controlled)"
    ),
    revision: str = typer.Option("", help="Dataset commit to download (default: the latest)"),
) -> None:
    revision = revision or HfApi().dataset_info(dataset).sha
    snapshot_download(dataset, repo_type="dataset", revision=revision, local_dir=output)
    (output / "REVISION").write_text(revision + "\n")
    RECORD.write_text(f"{dataset} {revision}\n")
    print(f"Downloaded {dataset} at {revision} to {output}; recorded in {RECORD} (commit this file)")


if __name__ == "__main__":
    app()
