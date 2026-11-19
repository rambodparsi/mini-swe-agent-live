# Patches: mini-swe-agent (gpt-6.1-sol) vs reference and other agents

Our runs: `runs/gpt-6.1-sol/b0__ee8df2`. Each task folder holds every source's `<name>_patch.diff` and the dataset's `reference_patch.diff` (gold).

Resolved (from each source's evaluation; `?` = no results file):

| Task | mini-swe-agent_gpt-6.1-sol_run_1 | mini-swe-agent_gpt-6.1-sol_run_2 | mini-swe-agent_gpt-6.1-sol_run_3 | TianxiCode-DeepSeek-Flash | Sapient-Slingshot-GPT-5.6-Sol | agav-GPT-5.5 |
|---|---|---|---|---|---|---|
| arviz-devs__arviz-2413 | no | no | no | yes | yes | no |
| deepset-ai__haystack-8525 | no | no | no | yes | yes | no |
| delgan__loguru-1306 | no | no | yes | yes | yes | yes |
| encode__starlette-2812 | yes | yes | yes | yes | yes | no |
| fonttools__fonttools-3682 | no | no | no | yes | yes | yes |
| iterative__dvc-10711 | yes | yes | yes | yes | yes | yes |
| pybamm-team__pybamm-4644 | yes | yes | yes | yes | yes | yes |
| sissbruecker__linkding-999 | no | no | no | yes | yes | yes |
| sphinx-doc__sphinx-13200 | no | no | no | yes | yes | yes |
| sympy__sympy-27462 | yes | yes | yes | yes | yes | yes |
