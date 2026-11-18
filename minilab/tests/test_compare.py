import xml.etree.ElementTree as ET

import pytest

from minilab.analysis.compare import (
    changed_lines,
    compare_all,
    compare_pair,
    jaccard,
    lcs,
    levenshtein,
    normalize_patch,
    touched_lines,
)
from minilab.analysis.figures import similarity_svg, timelines_svg
from minilab.tests.test_behavior import turns

PATCH_A = """diff --git a/pkg/mod.py b/pkg/mod.py
index 1111111..2222222 100644
--- a/pkg/mod.py
+++ b/pkg/mod.py
@@ -10,3 +10,3 @@ def f():
     x = 1
-    return x
+    return x + 1
"""
PATCH_B = PATCH_A.replace("index 1111111..2222222", "index 3333333..4444444")
PATCH_C = """diff --git a/pkg/mod.py b/pkg/mod.py
--- a/pkg/mod.py
+++ b/pkg/mod.py
@@ -11,2 +11,3 @@ def f():
-    return x
+    y = x + 1
+    return y
diff --git a/pkg/other.py b/pkg/other.py
--- a/pkg/other.py
+++ b/pkg/other.py
@@ -1 +1 @@
-a = 1
+a = 2
"""


@pytest.mark.parametrize(
    ("a", "b", "distance", "common"),
    [
        ("EEMTU", "EEMTU", 0, 5),
        ("EEMTU", "EMTU", 1, 4),
        ("EMTU", "ETMU", 2, 3),
        ("", "EMT", 3, 0),
        ("EET", "MMU", 3, 0),
    ],
)
def test_levenshtein_and_lcs(a, b, distance, common):
    assert (levenshtein(list(a), list(b)), lcs(list(a), list(b))) == (distance, common)
    assert (levenshtein(list(b), list(a)), lcs(list(b), list(a))) == (distance, common)


def test_patch_measures():
    assert jaccard(set(), set()) == 1.0 and jaccard({1, 2}, {2, 3}) == 1 / 3
    assert normalize_patch(PATCH_A) == normalize_patch(PATCH_B) != normalize_patch(PATCH_C)
    assert changed_lines(PATCH_A) == {("pkg/mod.py", "-", "return x"), ("pkg/mod.py", "+", "return x + 1")}
    assert changed_lines(PATCH_C) & changed_lines(PATCH_A) == {("pkg/mod.py", "-", "return x")}
    assert touched_lines(PATCH_A) == {("pkg/mod.py", n) for n in (10, 11, 12)}
    assert touched_lines(PATCH_C) == {("pkg/mod.py", 11), ("pkg/mod.py", 12), ("pkg/other.py", 1)}


def profile(seed: str, timeline: str, patch: str, resolved: bool, explored: str = "a.py;b.py") -> tuple[dict, list]:
    modified = ";".join(
        sorted({line.split(" b/", 1)[1] for line in patch.splitlines() if line.startswith("diff --git")})
    )
    row = {
        "condition": "b0", "instance_id": "t-1", "seed": seed, "resolved": resolved, "patch": patch,
        "explored_files": explored, "modified_files": modified, "timeline": " ".join(timeline),
        "turns": len(timeline), "cost": 0.1, "error_turns": 0, "explore_turns": timeline.count("E"),
        "modify_turns": timeline.count("M"), "test_turns": timeline.count("T"), "test_runner_turns": 0,
        "files_explored": len(explored.split(";")), "files_modified": len(modified.split(";")), "lines_added": 1,
        "lines_removed": 1, "exploration_ratio": 0.5, "modification_ratio": 0.2, "test_ratio": 0.2,
        "error_rate": 0.0, "transition_entropy": 1.0, "first_modification_timing": None,
    }  # fmt: skip
    return row, turns(timeline)


def test_compare_pair_by_hand():
    pair = compare_pair(profile("s1", "EEMTU", PATCH_A, True), profile("s2", "EMTU", PATCH_C, False, "a.py"))
    assert (pair["same_outcome"], pair["edit_distance"], pair["sequence_similarity"], pair["lcs_ratio"]) == (
        False,
        1,
        0.8,
        0.8,
    )
    assert pair["transition_jaccard"] == 3 / 4
    assert (pair["explored_files_jaccard"], pair["modified_files_jaccard"], pair["same_modified_files"]) == (
        0.5,
        0.5,
        False,
    )
    assert (pair["identical_patch"], pair["changed_lines_jaccard"], pair["touched_lines_jaccard"]) == (
        False,
        1 / 6,
        2 / 4,
    )
    same = compare_pair(profile("s1", "EMT", PATCH_A, True), profile("s2", "EMT", PATCH_B, True))
    assert (same["identical_sequence"], same["identical_patch"], same["patch_text_similarity"]) == (True, True, 1.0)


def test_compare_all_groups_by_task_and_draws_figures():
    runs = [
        profile("s1", "EEMTU", PATCH_A, True),
        profile("s2", "EMTU", PATCH_C, False),
        profile("s3", "EEMTU", PATCH_B, True),
    ]
    single = profile("s1", "EMT", PATCH_A, True)
    single[0]["instance_id"] = "t-2"
    pairwise, issues, spread = compare_all([runs[2], single, runs[0], runs[1]])
    assert [(p["run_a"], p["run_b"]) for p in pairwise] == [("s1", "s2"), ("s1", "s3"), ("s2", "s3")]
    assert len(issues) == 1 and {s["instance_id"] for s in spread} == {"t-1"}
    issue = issues[0]
    assert (
        issue["resolved_runs"],
        issue["outcome_consistent"],
        issue["distinct_sequences"],
        issue["distinct_patches"],
    ) == (
        2,
        False,
        2,
        2,
    )
    assert issue["identical_patch_pairs"] == 1 and issue["turns_range"] == 1
    turns_row = next(s for s in spread if s["feature"] == "turns")
    assert (turns_row["s1"], turns_row["s2"], turns_row["min"], turns_row["max"], turns_row["range"]) == (5, 4, 4, 5, 1)
    tasks = [[r for r, _ in runs], [single[0]]]
    by_run = {(r["instance_id"], r["seed"]): t for r, t in [*runs, single]}
    for drawing in (timelines_svg("b0", tasks, by_run), similarity_svg("b0", issues)):
        root = ET.fromstring(drawing)
        assert root.tag.endswith("svg") and root.findall(".//{http://www.w3.org/2000/svg}rect")
    assert timelines_svg("b0", tasks, by_run).count("<title>") == 5 + 4 + 5 + 3
