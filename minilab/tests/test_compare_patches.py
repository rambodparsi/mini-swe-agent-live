import json

from minilab.scripts.compare_patches import condition_dir, write_compare


def preds(path, patches):
    path.mkdir(parents=True, exist_ok=True)
    (path / "preds.json").write_text(json.dumps({k: {"model_patch": v} for k, v in patches.items()}))


def test_write_compare(tmp_path):
    condition = tmp_path / "runs" / "m" / "b0__abc"
    preds(condition / "s1", {"a": "p1a", "b": "p1b"})
    preds(condition / "s2", {"a": "p2a", "b": ""})
    (condition / "s1" / "eval").mkdir()
    (condition / "s1" / "eval" / "results.json").write_text(json.dumps({"success_ids": ["a"]}))
    preds(tmp_path / "other", {"a": "oa", "c": "oc"})
    (tmp_path / "other" / "results.json").write_text(json.dumps({"success_ids": ["a", "c"]}))
    out = tmp_path / "out"
    others = {"X": tmp_path / "other" / "preds.json"}
    assert write_compare(condition, "m", {"a": "gold a"}, others, out) == ["a", "b"]
    assert sorted(p.name for p in (out / "a").iterdir()) == [
        "X_patch.diff",
        "mini-swe-agent_m_run_1_patch.diff",
        "mini-swe-agent_m_run_2_patch.diff",
        "reference_patch.diff",
    ]
    assert (out / "a" / "X_patch.diff").read_text() == "oa"
    assert (out / "b" / "mini-swe-agent_m_run_2_patch.diff").read_text() == ""
    assert not (out / "c").exists()
    assert not (out / "b" / "reference_patch.diff").exists()
    readme = (out / "README.md").read_text()
    assert "| a | yes | ? | yes |" in readme
    assert "| b | no | ? | no |" in readme
    assert condition_dir(tmp_path / "runs", "m", "b0") == condition
