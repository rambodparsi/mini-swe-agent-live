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
├── README.md     this file
├── configs/      YAML configs for SWE-bench-Live runs
└── scripts/      helper scripts (dataset check, smoke test, evaluation)
```

Run outputs (`runs/`, `logs/`) are written outside version control.

## Changes to the original code

Every change to files outside `swelive/` is listed here.

| File | Change | Why |
|---|---|---|
| `src/minisweagent/run/benchmarks/swebench.py` | Docker image name for instances without an `image_name`/`docker_image` field comes from the config key `run.image_name_template` (Jinja, instance fields available). The default is the original SWE-bench naming, so behaviour without the key is unchanged. | SWE-bench-Live images are named `starryzhang/sweb.eval.x86_64.<id>`, not `swebench/...`. |
| `tests/run/test_swebench.py` | Two tests for the template (direct call and via config). | |

## Setup and running

Added in the next steps.

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
