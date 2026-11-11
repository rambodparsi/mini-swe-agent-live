# mini-swe-agent-live

This fork runs [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent) on
[SWE-bench-Live](https://github.com/microsoft/SWE-bench-Live) (lite split) for a research project.
Everything specific to this fork lives in this `swelive/` folder; the original code stays in `src/minisweagent/`.

## Starting point

| | |
|---|---|
| Upstream | [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) |
| Forked at | `04d809c` (v2.4.6 + 3 commits, 2026-09-03) |
| Reference branch | `upstream-base` (never changes; `git diff upstream-base main` shows all changes of this fork) |

To pull later upstream changes:

```bash
git remote add upstream https://github.com/SWE-agent/mini-swe-agent.git
git fetch upstream && git merge upstream/main
```

## Layout

```
swelive/
├── README.md                 this file
├── configs/swelive.yaml      SWE-bench-Live settings, used on top of the built-in swebench.yaml
└── scripts/
    ├── check_dataset.py      split size, fields, Docker image names; optionally checks that images exist
    └── smoke.sh              dataset check → gold patches → agent → evaluation, on the first N instances
```

Run outputs (`runs/`, `logs/`) are not version-controlled.

## Changes to the original code

Every change to files outside `swelive/` is listed here.

| File | Change | Why |
|---|---|---|
| `src/minisweagent/run/benchmarks/swebench.py` | Docker image name for instances without an `image_name`/`docker_image` field comes from the config key `run.image_name_template` (Jinja, instance fields available). The default is the original SWE-bench naming, so behaviour without the key is unchanged. | SWE-bench-Live images are named `starryzhang/sweb.eval.x86_64.<id>`, not `swebench/...`. |
| `tests/run/test_swebench.py` | Two tests for the template (direct call and via config). | |

## Setup (Linux)

Requirements: git, Python ≥ 3.10 (3.12 for the evaluator), Docker (your user in the `docker` group), an OpenAI API key.
SWE-bench-Live suggests about 4 CPUs and 16 GB RAM per parallel task, and images need plenty of disk space.

```bash
# 1. This repository
git clone https://github.com/rambodparsi/mini-swe-agent-live.git
cd mini-swe-agent-live
git remote add upstream https://github.com/SWE-agent/mini-swe-agent.git
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
mini-extra config set OPENAI_API_KEY sk-...      # stored outside the repository

# 2. SWE-bench-Live evaluator, next to this repository, in its own environment
git clone --recursive https://github.com/microsoft/SWE-bench-Live.git ../SWE-bench-Live
python3.12 -m venv ../SWE-bench-Live/.venv
../SWE-bench-Live/.venv/bin/pip install -e ../SWE-bench-Live ../SWE-bench-Live/launch

# 3. Check
docker run --rm hello-world
python swelive/scripts/check_dataset.py -n 2 --check-images
```

## Running

Smoke test on the first 2 instances (from the repository root, with `.venv` active):

```bash
bash swelive/scripts/smoke.sh                   # N=2 WORKERS=2 by default; e.g. N=5 bash swelive/scripts/smoke.sh
```

It writes `runs/smoke_<date>_<time>/`:

| Path | Content |
|---|---|
| `instance_ids.txt` | the instances used |
| `eval_gold/` | evaluator results for the dataset's gold patches (checks the setup) |
| `agent/preds.json` | the agent's patches |
| `agent/<instance_id>/<instance_id>.traj.json` | full trajectory: every model message, command and output |
| `agent/exit_statuses_*.yaml` | how each run ended (`Submitted`, `LimitsExceeded`, errors) |
| `eval_agent/` | evaluator results for the agent's patches; `<instance_id>/report.json` per instance |

The two steps separately:

```bash
mini-extra swebench -c swebench.yaml -c swelive/configs/swelive.yaml \
  --subset SWE-bench-Live/SWE-bench-Live --split lite --slice 0:30 -w 4 -o runs/pilot

cd ../SWE-bench-Live && .venv/bin/python -m evaluation.evaluation \
  --dataset SWE-bench-Live/SWE-bench-Live --split lite --platform linux \
  --patch_dir "$OLDPWD/runs/pilot/preds.json" --output_dir "$OLDPWD/runs/pilot/eval" --workers 4 --overwrite 0
```

Browse trajectories with `mini-extra inspect runs/pilot`.

## License and credit

mini-SWE-agent is MIT-licensed, © 2025 Kilian A. Lieret and Carlos E. Jimenez (see [`LICENSE.md`](../LICENSE.md)).
The license and copyright notice of the original project are kept unchanged.
The SWE-bench-Live dataset and evaluator are by Microsoft (MIT license).

## Citations

```bibtex
@inproceedings{yang2024sweagent,
  title={{SWE}-agent: Agent-Computer Interfaces Enable Automated Software Engineering},
  author={John Yang and Carlos E Jimenez and Alexander Wettig and Kilian Lieret and Shunyu Yao and Karthik R Narasimhan and Ofir Press},
  booktitle={The Thirty-eighth Annual Conference on Neural Information Processing Systems},
  year={2024},
  url={https://arxiv.org/abs/2405.15793}
}

@article{zhang2025swebenchgoeslive,
  title={SWE-bench Goes Live!},
  author={Linghao Zhang and Shilin He and Chaoyun Zhang and Yu Kang and Bowen Li and Chengxing Xie and Junhao Wang and Maoquan Wang and Yufan Huang and Shengyu Fu and Elsie Nallipogu and Qingwei Lin and Yingnong Dang and Saravan Rajmohan and Dongmei Zhang},
  journal={Advances in Neural Information Processing Systems},
  volume={38},
  year={2025}
}

@inproceedings{jimenez2024swebench,
  title={{SWE}-bench: Can Language Models Resolve Real-World {GitHub} Issues?},
  author={Carlos E Jimenez and John Yang and Alexander Wettig and Shunyu Yao and Kexin Pei and Ofir Press and Karthik R Narasimhan},
  booktitle={The Twelfth International Conference on Learning Representations},
  year={2024},
  url={https://openreview.net/forum?id=VTF8yNQM66}
}
```
