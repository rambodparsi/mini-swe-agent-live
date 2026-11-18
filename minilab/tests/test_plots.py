import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from typer.testing import CliRunner

from minilab.analysis.behavior import app
from minilab.analysis.plots import (
    agreement_rows,
    agreement_svg,
    effect_svg,
    errors_svg,
    nice_ticks,
    outcome_svg,
    path_code_svg,
    phases_svg,
    shift_svg,
    spread_svg,
    swarm,
    transitions_svg,
)
from minilab.tests.test_analysis import make_run
from minilab.tests.test_compare import PATCH_A, PATCH_B, PATCH_C, profile

SVG = "{http://www.w3.org/2000/svg}"


@pytest.mark.parametrize(
    ("value", "ticks"),
    [
        (29, [0, 10, 20, 30]),
        (15, [0, 5, 10, 15]),
        (0.124, [0, 0.05, 0.1, 0.15]),
        (77, [0, 20, 40, 60, 80]),
        (0, [0, 0.25, 0.5, 0.75, 1]),
    ],
)
def test_nice_ticks(value, ticks):
    assert nice_ticks(value) == ticks


def test_swarm_keeps_dots_apart():
    ys = [100, 100, 100, 104, 140]
    offsets = swarm(ys, radius=4.5)
    assert offsets[0] == 0 and offsets[-1] == 0
    assert all((offsets[i] - offsets[j]) ** 2 + (ys[i] - ys[j]) ** 2 >= 100 for i in range(5) for j in range(i))


def test_agreement_rows_by_hand():
    runs = [
        profile("s1", "EMT", PATCH_A, True)[0],
        profile("s2", "EMT", PATCH_B, True)[0],
        profile("s3", "EMT", PATCH_C, False)[0],
    ]
    assert agreement_rows([runs]) == [{
        "condition": "b0", "instance_id": "t-1", "runs": 3, "resolved_runs": 2, "changed_lines": 6,
        "in_all_runs": 1, "in_some_runs": 1, "in_one_run": 4,
    }]  # fmt: skip


def test_every_figure_is_valid_svg_with_hover_titles():
    runs = [
        profile("s1", "EEMTU", PATCH_A, True),
        profile("s2", "EMTU", PATCH_C, False),
        profile("s3", "EEMTU", PATCH_B, True),
    ]
    rows = [r for r, _ in runs]
    for r in rows:
        r.update({"errors_command_not_found": 1 if r["seed"] != "s2" else 0, "errors_test_failure": 0})
    pairs = [{"instance_id": "t-1", "run_a": "s1", "run_b": "s2", "sequence_similarity": 0.8,
              "changed_lines_jaccard": 1 / 6, "same_outcome": False}]  # fmt: skip
    means = {"b0": {"exploration_ratio": 0.4, "P7_test_after_modify": 0.8}, "p1": {"exploration_ratio": 0.3}}
    drawings = [
        phases_svg("b0", [t for _, t in runs]),
        transitions_svg("b0", [t for _, t in runs]),
        errors_svg("b0", rows),
        outcome_svg("b0", rows),
        spread_svg("b0", [rows]),
        path_code_svg("b0", pairs),
        agreement_svg("b0", agreement_rows([rows])),
        effect_svg("b0", "p1", [("t-1", 0.5), ("t-2", -1.0)], {"diff": -0.25, "ci95": [-1.0, 0.5]}),
        shift_svg(["b0", "p1"], means),
    ]
    for drawing in drawings:
        root = ET.fromstring(drawing)
        assert root.tag == f"{SVG}svg" and root.findall(f".//{SVG}title")
    assert "2 error turns in 3 runs" in drawings[2] and "in 2 of 3 runs" in drawings[2]
    assert "+0.50" in drawings[7] and "-0.25 [-1.00, +0.50]" in drawings[7]
    transitions = drawings[1]
    assert "start → Exploration: 3" in transitions and "Utility → end: 3" in transitions


def resolved_runs(run: Path, resolved: dict[str, list[str]]) -> None:
    for seed, ids in resolved.items():
        (run / seed / "eval" / "results.json").write_text(json.dumps({"success_ids": ids}))


def test_cli_draws_condition_figures_and_checks_baseline(tmp_path):
    for name in ("b0__aaa", "p1__bbb"):
        for seed in ("s1", "s2"):
            make_run(tmp_path, tmp_path / "runs" / name / seed, name.startswith("p1"), [])
    resolved_runs(tmp_path / "runs" / "p1__bbb", {"s1": ["repo__x-1"], "s2": ["repo__x-1", "repo__x-2"]})
    out = tmp_path / "out"
    folders = [str(tmp_path / "runs" / n) for n in ("b0__aaa", "p1__bbb")]
    result = CliRunner().invoke(app, [*folders, "--baseline", "b0", "-o", str(out)])
    assert result.exit_code == 0, result.output
    names = {f.name for f in (out / "summary" / "figures").iterdir()}
    per_condition = {
        "timelines",
        "phases",
        "transitions",
        "errors",
        "spread",
        "outcome",
        "similarity",
        "path_vs_code",
        "agreement",
    }
    assert names == {f"{c}__{k}.svg" for c in ("b0__aaa", "p1__bbb") for k in per_condition} | {
        "process_shift__b0__aaa.svg",
        "effect__p1__bbb__vs__b0__aaa.svg",
    }
    effect = (out / "summary" / "figures" / "effect__p1__bbb__vs__b0__aaa.svg").read_text()
    assert "repo__x-1: +1.00" in effect and "repo__x-2: +0.50" in effect
    assert (out / "level2" / "changed_line_agreement.csv").exists()
    assert CliRunner().invoke(app, [*folders, "--baseline", "nope", "-o", str(out)]).exit_code == 2
