"""Write the fixed pilot task list: a seeded sample of the split, spread over repositories (round-robin).

python minilab/scripts/make_pilot.py -n 30            # writes minilab/configs/pilot_instances.txt
"""

import random
from pathlib import Path

import typer
from datasets import load_dataset

app = typer.Typer(add_completion=False)
OUT = Path(__file__).parents[1] / "configs" / "pilot_instances.txt"


def pick(instances: list[dict], n: int, seed: int) -> list[str]:
    by_repo: dict[str, list[str]] = {}
    for i in sorted(instances, key=lambda i: i["instance_id"]):
        by_repo.setdefault(i["repo"], []).append(i["instance_id"])
    rng = random.Random(seed)
    queues = [rng.sample(ids, len(ids)) for _, ids in sorted(by_repo.items())]
    rng.shuffle(queues)
    order = [q[k] for k in range(max(map(len, queues))) for q in queues if k < len(q)]
    return sorted(order[:n])


@app.command()
def main(
    n: int = typer.Option(30, "-n", help="Number of tasks"),
    seed: int = typer.Option(0, help="Sampling seed"),
    dataset: str = typer.Option("SWE-bench-Live/SWE-bench-Live", help="Hugging Face dataset name"),
    split: str = typer.Option("lite", help="Dataset split"),
    output: Path = typer.Option(OUT, "-o", "--output"),
) -> None:
    ids = pick(list(load_dataset(dataset, split=split)), n, seed)
    output.write_text("\n".join(ids) + "\n")
    print(f"Wrote {len(ids)} tasks from {dataset} [{split}], seed {seed}, to {output}")


if __name__ == "__main__":
    app()
