# Leaderboard submissions: predictions and trajectories (SWE-bench-Live lite)

Copied from [SWE-bench-Live/submission](https://github.com/SWE-bench-Live/submission) at commit
`501f80da7097e11af41a5eead8e554c661a6cb4d` (2026-11-15), MIT license (see [`LICENSE`](LICENSE)).
Files are unchanged; only the folder layout is ours: `<submission>/preds/preds.json`, `<submission>/results/results.json`
(the submission's evaluation summary) and `<submission>/trajs/`.

**[`TABLES.md`](TABLES.md)**: which submission resolved which task, which has a trajectory for which task, and the tasks resolved by all or by none of the submissions
(also as `resolved_by_instance.csv` and `trajectories_by_instance.csv`). Rebuild with
`python -m minilab.scripts.leaderboard_tables patch_diff/mini-swe-agent_vs_leaderboards_preds_and_trajs`.
A task counts as resolved if it is in the submission's resolved list; otherwise it is empty (no patch), error,
incomplete or failed, in that order. ami-agent's `results.json` lists one empty patch as resolved and 6 resolved tasks
also as errors; the resolved list is followed.

| Folder | Source (`submissions/lite/...`) | preds.json | Trajectories |
|---|---|---|---|
| `tianxicode_deepseek-flash` | `tianxicode/deepseek-flash` | 300 tasks | 300 folders: `events.jsonl`, `trajectory.md`, `prompt.txt`, `patch.diff`, `patch.diag.diff`, `meta.json`, `git-status.txt` |
| `sapient-slingshot-agent_v3.4.0_gpt-5.6-sol` | `sapient-slingshot-agent/v3.4.0/gpt-5.6-sol` | 300 tasks | 14 tasks only, one `<task>.md` each |
| `ami-agent` | `ami-agent/20260623-v0.7.0-claude-opus-4-6` | 300 tasks | 290 tasks, one `<task>.json` each |
| `agav_gpt-5.5` | `agav/gpt-5.5` | 300 tasks | 3 tasks only, one `<task>.txt` each |

Not copied: evaluation logs, the submissions' READMEs and ami-agent's helper scripts. They are in the source
repository at the commit above.
