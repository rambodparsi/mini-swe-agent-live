# Leaderboard submissions per task

How 4 SWE-bench-Live **lite** leaderboard submissions did on each of the 300 tasks, and which of them published a trajectory. Source, commit and license of the data: [`README.md`](README.md). Rebuild this page with `python -m minilab.scripts.leaderboard_tables patch_diff/mini-swe-agent_vs_leaderboards_preds_and_trajs`; the full per-task data is also in `resolved_by_instance.csv` and `trajectories_by_instance.csv`.

## Summary

| submission | resolved | failed | empty patch | eval. error | not evaluated | trajectories | format |
|---|---|---|---|---|---|---|---|
| tianxicode_deepseek-flash | **213** (71.0%) | 87 | 0 | 0 | 0 | 300/300 | folder |
| sapient-slingshot-agent_v3.4.0_gpt-5.6-sol | **211** (70.3%) | 89 | 0 | 0 | 0 | 14/300 | md |
| ami-agent | **189** (63.0%) | 99 | 9 | 3 | 0 | 290/300 | json |
| agav_gpt-5.5 | **186** (62.0%) | 85 | 29 | 0 | 0 | 3/300 | txt |

- Tasks by number of submissions that resolved them: 4 of 4: 102, 3 of 4: 77, 2 of 4: 52, 1 of 4: 56, 0 of 4: 13.
- Outcomes come from each submission's `results/results.json`; a task in its resolved list counts as resolved, otherwise it is an empty patch, evaluation error, not evaluated or failed, in that order.
- Legend used in all tables: ✅ resolved · ❌ failed (the patch did not pass the tests) · ⬜ empty patch · ⚠️ evaluation error · … not evaluated.

## Contents

- [1. Resolved per task](#1-resolved-per-task): every task × every submission, with how many submissions resolved each task
- [2. Trajectory per task](#2-trajectory-per-task): which submission has a trajectory for which task, and in which format
- [3. Resolved by all submissions (102 tasks)](#3-resolved-by-all-submissions-102-tasks): the tasks every submission solved
- [4. Resolved by none (13 tasks)](#4-resolved-by-none-13-tasks): the tasks no submission solved
- [5. tianxicode_deepseek-flash vs ami-agent](#5-tianxicode_deepseek-flash-vs-ami-agent): tasks one of the two resolved and the other did not
  - [5a. Resolved by tianxicode_deepseek-flash, not by ami-agent (80 tasks)](#5a-resolved-by-tianxicode_deepseek-flash-not-by-ami-agent-80-tasks): tianxicode_deepseek-flash ✅, ami-agent not
  - [5b. Resolved by ami-agent, not by tianxicode_deepseek-flash (56 tasks)](#5b-resolved-by-ami-agent-not-by-tianxicode_deepseek-flash-56-tasks): ami-agent ✅, tianxicode_deepseek-flash not

## 1. Resolved per task

Columns are ordered by number of resolved tasks.

| instance_id | tianxicode_deepseek-flash | sapient-slingshot-agent_v3.4.0_gpt-5.6-sol | ami-agent | agav_gpt-5.5 | resolved by |
|---|---|---|---|---|---|
| **resolved** | **213/300** | **211/300** | **189/300** | **186/300** |  |
| aiogram__aiogram-1594 | ✅ | ✅ | ❌ | ✅ | 3 |
| amoffat__sh-744 | ✅ | ❌ | ✅ | ❌ | 2 |
| arviz-devs__arviz-2413 | ✅ | ✅ | ❌ | ⬜ | 2 |
| aws-cloudformation__cfn-lint-3749 | ✅ | ✅ | ❌ | ✅ | 3 |
| aws-cloudformation__cfn-lint-3764 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3767 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3768 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3770 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3779 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3789 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3798 | ❌ | ❌ | ❌ | ❌ | 0 |
| aws-cloudformation__cfn-lint-3805 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3817 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3821 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3854 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3855 | ❌ | ❌ | ❌ | ❌ | 0 |
| aws-cloudformation__cfn-lint-3856 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3862 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3866 | ❌ | ❌ | ❌ | ❌ | 0 |
| aws-cloudformation__cfn-lint-3875 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3890 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3947 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-3982 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-4002 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-4009 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-4016 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-4023 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-4032 | ❌ | ❌ | ✅ | ❌ | 1 |
| aws-cloudformation__cfn-lint-4051 | ❌ | ❌ | ✅ | ❌ | 1 |
| beancount__beancount-931 | ✅ | ✅ | ✅ | ✅ | 4 |
| beetbox__beets-5457 | ✅ | ✅ | ✅ | ✅ | 4 |
| beetbox__beets-5495 | ✅ | ✅ | ✅ | ✅ | 4 |
| beetbox__beets-5682 | ✅ | ✅ | ❌ | ❌ | 2 |
| beeware__briefcase-2075 | ✅ | ✅ | ✅ | ⬜ | 3 |
| beeware__briefcase-2085 | ✅ | ✅ | ✅ | ✅ | 4 |
| beeware__briefcase-2088 | ❌ | ✅ | ✅ | ✅ | 3 |
| beeware__briefcase-2214 | ❌ | ❌ | ✅ | ✅ | 2 |
| bridgecrewio__checkov-6893 | ❌ | ❌ | ✅ | ❌ | 1 |
| bridgecrewio__checkov-6895 | ❌ | ❌ | ❌ | ❌ | 0 |
| bridgecrewio__checkov-7002 | ❌ | ❌ | ✅ | ❌ | 1 |
| conan-io__conan-17092 | ✅ | ✅ | ❌ | ✅ | 3 |
| conan-io__conan-17102 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17117 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17123 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17129 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17132 | ✅ | ❌ | ❌ | ✅ | 2 |
| conan-io__conan-17183 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17266 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17292 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17300 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17301 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17302 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17326 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17366 | ✅ | ✅ | ❌ | ✅ | 3 |
| conan-io__conan-17382 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17408 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17514 | ✅ | ❌ | ❌ | ✅ | 2 |
| conan-io__conan-17517 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17520 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17532 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17538 | ❌ | ✅ | ⬜ | ❌ | 1 |
| conan-io__conan-17708 | ✅ | ✅ | ❌ | ⬜ | 2 |
| conan-io__conan-17725 | ✅ | ✅ | ❌ | ✅ | 3 |
| conan-io__conan-17781 | ✅ | ✅ | ❌ | ⬜ | 2 |
| conan-io__conan-17819 | ✅ | ✅ | ❌ | ⬜ | 2 |
| conan-io__conan-17917 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17923 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-17967 | ✅ | ✅ | ⬜ | ✅ | 3 |
| conan-io__conan-18028 | ✅ | ✅ | ✅ | ✅ | 4 |
| conan-io__conan-18037 | ✅ | ✅ | ✅ | ✅ | 4 |
| cyclotruc__gitingest-115 | ✅ | ❌ | ✅ | ❌ | 2 |
| cyclotruc__gitingest-134 | ❌ | ❌ | ❌ | ❌ | 0 |
| cyclotruc__gitingest-94 | ✅ | ✅ | ✅ | ✅ | 4 |
| deepset-ai__haystack-8489 | ✅ | ✅ | ❌ | ✅ | 3 |
| deepset-ai__haystack-8525 | ✅ | ✅ | ❌ | ⬜ | 2 |
| deepset-ai__haystack-8609 | ✅ | ✅ | ✅ | ✅ | 4 |
| deepset-ai__haystack-8619 | ✅ | ❌ | ❌ | ✅ | 2 |
| deepset-ai__haystack-8725 | ✅ | ✅ | ✅ | ✅ | 4 |
| deepset-ai__haystack-8799 | ✅ | ✅ | ✅ | ✅ | 4 |
| deepset-ai__haystack-8879 | ✅ | ❌ | ❌ | ⬜ | 1 |
| deepset-ai__haystack-8940 | ✅ | ❌ | ✅ | ✅ | 3 |
| deepset-ai__haystack-8969 | ✅ | ✅ | ✅ | ✅ | 4 |
| deepset-ai__haystack-8973 | ✅ | ✅ | ✅ | ✅ | 4 |
| deepset-ai__haystack-8981 | ✅ | ✅ | ❌ | ✅ | 3 |
| deepset-ai__haystack-8992 | ✅ | ✅ | ✅ | ✅ | 4 |
| deepset-ai__haystack-8993 | ✅ | ✅ | ❌ | ✅ | 3 |
| deepset-ai__haystack-8997 | ✅ | ✅ | ✅ | ✅ | 4 |
| deepset-ai__haystack-9027 | ✅ | ✅ | ❌ | ⬜ | 2 |
| deepset-ai__haystack-9066 | ✅ | ✅ | ✅ | ⬜ | 3 |
| delgan__loguru-1297 | ✅ | ✅ | ✅ | ✅ | 4 |
| delgan__loguru-1306 | ✅ | ✅ | ✅ | ✅ | 4 |
| dynaconf__dynaconf-1225 | ✅ | ✅ | ✅ | ✅ | 4 |
| dynaconf__dynaconf-1238 | ✅ | ✅ | ❌ | ✅ | 3 |
| dynaconf__dynaconf-1241 | ✅ | ✅ | ✅ | ✅ | 4 |
| dynaconf__dynaconf-1249 | ✅ | ✅ | ✅ | ⬜ | 3 |
| encode__starlette-2812 | ✅ | ✅ | ❌ | ⬜ | 2 |
| facebookresearch__hydra-3005 | ✅ | ✅ | ❌ | ✅ | 3 |
| falconry__falcon-2366 | ✅ | ✅ | ❌ | ✅ | 3 |
| falconry__falcon-2419 | ❌ | ✅ | ✅ | ⬜ | 2 |
| feast-dev__feast-5036 | ✅ | ✅ | ✅ | ✅ | 4 |
| flexget__flexget-4244 | ✅ | ✅ | ✅ | ✅ | 4 |
| flexget__flexget-4306 | ✅ | ✅ | ✅ | ⬜ | 3 |
| fonttools__fonttools-3682 | ✅ | ✅ | ✅ | ✅ | 4 |
| fonttools__fonttools-3726 | ❌ | ✅ | ✅ | ❌ | 2 |
| geopandas__geopandas-3471 | ❌ | ❌ | ✅ | ❌ | 1 |
| hiyouga__llama-factory-7505 | ❌ | ✅ | ⬜ | ⬜ | 1 |
| huggingface__smolagents-285 | ❌ | ❌ | ✅ | ❌ | 1 |
| huggingface__smolagents-405 | ❌ | ❌ | ✅ | ❌ | 1 |
| huggingface__smolagents-731 | ❌ | ❌ | ❌ | ❌ | 0 |
| huggingface__smolagents-843 | ❌ | ❌ | ✅ | ❌ | 1 |
| icloud-photos-downloader__icloud_photos_downloader-1060 | ✅ | ✅ | ✅ | ✅ | 4 |
| instructlab__instructlab-2526 | ❌ | ✅ | ✅ | ✅ | 3 |
| instructlab__instructlab-2540 | ❌ | ✅ | ✅ | ✅ | 3 |
| instructlab__instructlab-2548 | ✅ | ✅ | ✅ | ✅ | 4 |
| instructlab__instructlab-2572 | ❌ | ✅ | ❌ | ✅ | 2 |
| instructlab__instructlab-2585 | ✅ | ✅ | ❌ | ⬜ | 2 |
| instructlab__instructlab-2592 | ❌ | ✅ | ❌ | ❌ | 1 |
| instructlab__instructlab-2825 | ❌ | ✅ | ❌ | ❌ | 1 |
| instructlab__instructlab-2886 | ✅ | ✅ | ❌ | ✅ | 3 |
| instructlab__instructlab-2927 | ✅ | ✅ | ❌ | ✅ | 3 |
| instructlab__instructlab-3060 | ❌ | ✅ | ✅ | ❌ | 2 |
| instructlab__instructlab-3118 | ❌ | ❌ | ✅ | ✅ | 2 |
| ipython__ipython-14695 | ✅ | ✅ | ✅ | ✅ | 4 |
| ipython__ipython-14798 | ✅ | ❌ | ✅ | ✅ | 3 |
| ipython__ipython-14822 | ✅ | ✅ | ✅ | ✅ | 4 |
| ipython__ipython-14838 | ✅ | ✅ | ✅ | ✅ | 4 |
| iterative__dvc-10711 | ✅ | ✅ | ✅ | ✅ | 4 |
| jazzband__tablib-613 | ✅ | ✅ | ❌ | ✅ | 3 |
| joke2k__faker-2142 | ❌ | ❌ | ❌ | ❌ | 0 |
| joke2k__faker-2155 | ✅ | ✅ | ✅ | ✅ | 4 |
| joke2k__faker-2162 | ❌ | ✅ | ✅ | ❌ | 2 |
| joke2k__faker-2173 | ✅ | ✅ | ✅ | ✅ | 4 |
| joke2k__faker-2190 | ✅ | ✅ | ✅ | ✅ | 4 |
| jupyterlab__jupyter-ai-1022 | ✅ | ✅ | ❌ | ✅ | 3 |
| jupyterlab__jupyter-ai-1125 | ✅ | ✅ | ⚠️ | ✅ | 3 |
| jupyterlab__jupyter-ai-1294 | ✅ | ✅ | ✅ | ✅ | 4 |
| kedro-org__kedro-4387 | ❌ | ❌ | ✅ | ⬜ | 1 |
| kedro-org__kedro-4406 | ❌ | ❌ | ✅ | ❌ | 1 |
| kedro-org__kedro-4408 | ❌ | ❌ | ✅ | ❌ | 1 |
| kedro-org__kedro-4427 | ❌ | ❌ | ✅ | ⬜ | 1 |
| kedro-org__kedro-4580 | ❌ | ❌ | ❌ | ❌ | 0 |
| keras-team__keras-20389 | ✅ | ❌ | ✅ | ✅ | 3 |
| keras-team__keras-20396 | ✅ | ❌ | ❌ | ✅ | 2 |
| keras-team__keras-20443 | ✅ | ❌ | ✅ | ✅ | 3 |
| keras-team__keras-20534 | ✅ | ❌ | ❌ | ✅ | 2 |
| keras-team__keras-20609 | ✅ | ❌ | ✅ | ✅ | 3 |
| keras-team__keras-20880 | ✅ | ❌ | ❌ | ✅ | 2 |
| keras-team__keras-21072 | ✅ | ❌ | ✅ | ✅ | 3 |
| koxudaxi__datamodel-code-generator-2259 | ✅ | ✅ | ✅ | ✅ | 4 |
| koxudaxi__datamodel-code-generator-2327 | ✅ | ✅ | ✅ | ❌ | 3 |
| koxudaxi__datamodel-code-generator-2349 | ✅ | ✅ | ✅ | ✅ | 4 |
| kozea__weasyprint-2300 | ✅ | ✅ | ✅ | ✅ | 4 |
| kozea__weasyprint-2303 | ✅ | ✅ | ✅ | ✅ | 4 |
| kozea__weasyprint-2387 | ✅ | ✅ | ❌ | ✅ | 3 |
| kozea__weasyprint-2398 | ✅ | ✅ | ✅ | ✅ | 4 |
| kozea__weasyprint-2405 | ✅ | ✅ | ✅ | ✅ | 4 |
| kubernetes-client__python-2303 | ❌ | ✅ | ❌ | ❌ | 1 |
| matplotlib__matplotlib-28933 | ✅ | ❌ | ❌ | ❌ | 1 |
| matplotlib__matplotlib-29007 | ✅ | ❌ | ❌ | ⬜ | 1 |
| matplotlib__matplotlib-29249 | ✅ | ❌ | ✅ | ⬜ | 2 |
| matplotlib__matplotlib-29258 | ✅ | ❌ | ✅ | ❌ | 2 |
| matplotlib__matplotlib-29285 | ✅ | ❌ | ✅ | ❌ | 2 |
| matplotlib__matplotlib-29388 | ✅ | ❌ | ✅ | ❌ | 2 |
| matplotlib__matplotlib-29431 | ✅ | ❌ | ❌ | ❌ | 1 |
| matplotlib__matplotlib-29486 | ✅ | ❌ | ❌ | ❌ | 1 |
| matplotlib__matplotlib-29537 | ✅ | ❌ | ✅ | ❌ | 2 |
| matplotlib__matplotlib-29689 | ✅ | ❌ | ❌ | ❌ | 1 |
| matplotlib__matplotlib-29721 | ✅ | ❌ | ✅ | ✅ | 3 |
| matplotlib__matplotlib-29781 | ❌ | ❌ | ❌ | ❌ | 0 |
| mikedh__trimesh-2354 | ❌ | ❌ | ✅ | ❌ | 1 |
| mikedh__trimesh-2363 | ✅ | ❌ | ✅ | ✅ | 3 |
| modelcontextprotocol__python-sdk-167 | ✅ | ✅ | ✅ | ⬜ | 3 |
| modelcontextprotocol__python-sdk-222 | ✅ | ❌ | ❌ | ✅ | 2 |
| pallets__flask-5626 | ✅ | ✅ | ✅ | ✅ | 4 |
| pallets__flask-5637 | ✅ | ✅ | ✅ | ✅ | 4 |
| patroni__patroni-3198 | ✅ | ✅ | ✅ | ✅ | 4 |
| pdm-project__pdm-3237 | ✅ | ✅ | ❌ | ❌ | 2 |
| pdm-project__pdm-3250 | ✅ | ✅ | ❌ | ✅ | 3 |
| pdm-project__pdm-3255 | ✅ | ✅ | ✅ | ✅ | 4 |
| pdm-project__pdm-3314 | ✅ | ✅ | ❌ | ✅ | 3 |
| pdm-project__pdm-3374 | ✅ | ✅ | ❌ | ✅ | 3 |
| pdm-project__pdm-3419 | ✅ | ✅ | ⬜ | ❌ | 2 |
| pdm-project__pdm-3420 | ✅ | ✅ | ✅ | ✅ | 4 |
| privacyidea__privacyidea-4206 | ❌ | ✅ | ❌ | ✅ | 2 |
| privacyidea__privacyidea-4223 | ❌ | ✅ | ❌ | ✅ | 2 |
| privacyidea__privacyidea-4226 | ❌ | ✅ | ✅ | ✅ | 3 |
| privacyidea__privacyidea-4233 | ❌ | ✅ | ❌ | ✅ | 2 |
| privacyidea__privacyidea-4251 | ❌ | ✅ | ❌ | ✅ | 2 |
| projectmesa__mesa-2394 | ✅ | ✅ | ✅ | ✅ | 4 |
| projectmesa__mesa-2418 | ✅ | ✅ | ✅ | ✅ | 4 |
| projectmesa__mesa-2523 | ✅ | ✅ | ❌ | ✅ | 3 |
| projectmesa__mesa-2605 | ✅ | ✅ | ✅ | ❌ | 3 |
| projectmesa__mesa-2632 | ✅ | ✅ | ✅ | ✅ | 4 |
| pvlib__pvlib-python-2249 | ✅ | ✅ | ✅ | ✅ | 4 |
| pvlib__pvlib-python-2286 | ✅ | ✅ | ✅ | ✅ | 4 |
| pvlib__pvlib-python-2291 | ✅ | ✅ | ✅ | ✅ | 4 |
| pvlib__pvlib-python-2292 | ✅ | ✅ | ❌ | ✅ | 3 |
| pvlib__pvlib-python-2341 | ✅ | ✅ | ✅ | ✅ | 4 |
| pvlib__pvlib-python-2393 | ✅ | ✅ | ✅ | ✅ | 4 |
| pvlib__pvlib-python-2400 | ✅ | ✅ | ✅ | ✅ | 4 |
| pybamm-team__pybamm-4644 | ✅ | ✅ | ✅ | ✅ | 4 |
| pybamm-team__pybamm-4816 | ❌ | ✅ | ✅ | ❌ | 2 |
| pybamm-team__pybamm-4865 | ✅ | ✅ | ✅ | ✅ | 4 |
| pydata__xarray-10076 | ✅ | ✅ | ⬜ | ✅ | 3 |
| pydata__xarray-9586 | ✅ | ❌ | ✅ | ✅ | 3 |
| pydata__xarray-9636 | ❌ | ✅ | ❌ | ❌ | 1 |
| pydata__xarray-9760 | ✅ | ✅ | ❌ | ⬜ | 2 |
| pydata__xarray-9765 | ✅ | ✅ | ❌ | ✅ | 3 |
| pydata__xarray-9971 | ❌ | ✅ | ⬜ | ❌ | 1 |
| pydata__xarray-9974 | ✅ | ✅ | ✅ | ✅ | 4 |
| pylint-dev__pylint-10044 | ✅ | ✅ | ✅ | ❌ | 3 |
| pylint-dev__pylint-10062 | ✅ | ✅ | ✅ | ⬜ | 3 |
| pylint-dev__pylint-10089 | ✅ | ✅ | ✅ | ✅ | 4 |
| pylint-dev__pylint-10097 | ✅ | ✅ | ❌ | ✅ | 3 |
| pylint-dev__pylint-10240 | ✅ | ✅ | ❌ | ✅ | 3 |
| pypa__twine-1225 | ✅ | ✅ | ✅ | ✅ | 4 |
| pypsa__pypsa-1091 | ❌ | ❌ | ✅ | ❌ | 1 |
| pypsa__pypsa-1112 | ❌ | ❌ | ✅ | ❌ | 1 |
| pypsa__pypsa-1172 | ❌ | ❌ | ✅ | ❌ | 1 |
| pypsa__pypsa-1195 | ❌ | ❌ | ❌ | ❌ | 0 |
| python-babel__babel-1141 | ✅ | ✅ | ✅ | ✅ | 4 |
| python-babel__babel-1163 | ✅ | ✅ | ✅ | ✅ | 4 |
| python-babel__babel-1164 | ✅ | ❌ | ❌ | ✅ | 2 |
| python-babel__babel-1179 | ✅ | ✅ | ✅ | ✅ | 4 |
| python-babel__babel-1194 | ✅ | ✅ | ✅ | ✅ | 4 |
| python-control__python-control-1064 | ✅ | ❌ | ❌ | ❌ | 1 |
| python-control__python-control-1111 | ✅ | ✅ | ✅ | ✅ | 4 |
| python-control__python-control-1142 | ✅ | ✅ | ❌ | ✅ | 3 |
| python-telegram-bot__python-telegram-bot-4617 | ❌ | ❌ | ❌ | ❌ | 0 |
| python-telegram-bot__python-telegram-bot-4626 | ❌ | ❌ | ✅ | ❌ | 1 |
| python-telegram-bot__python-telegram-bot-4673 | ❌ | ❌ | ❌ | ❌ | 0 |
| pytorch__torchtune-1806 | ✅ | ✅ | ✅ | ✅ | 4 |
| pytorch__torchtune-2066 | ✅ | ✅ | ❌ | ✅ | 3 |
| pytorch__torchtune-2139 | ✅ | ✅ | ❌ | ⬜ | 2 |
| qtile__qtile-5154 | ✅ | ✅ | ❌ | ✅ | 3 |
| reata__sqllineage-661 | ✅ | ✅ | ✅ | ⬜ | 3 |
| reata__sqllineage-694 | ✅ | ❌ | ✅ | ✅ | 3 |
| reflex-dev__reflex-4087 | ✅ | ✅ | ✅ | ✅ | 4 |
| reflex-dev__reflex-4129 | ✅ | ✅ | ❌ | ❌ | 2 |
| reflex-dev__reflex-4266 | ✅ | ✅ | ✅ | ✅ | 4 |
| reflex-dev__reflex-4347 | ✅ | ✅ | ❌ | ✅ | 3 |
| reflex-dev__reflex-4371 | ✅ | ✅ | ⚠️ | ✅ | 3 |
| reflex-dev__reflex-4427 | ✅ | ✅ | ❌ | ✅ | 3 |
| reflex-dev__reflex-4510 | ✅ | ✅ | ✅ | ✅ | 4 |
| reflex-dev__reflex-4563 | ✅ | ❌ | ✅ | ✅ | 3 |
| reflex-dev__reflex-4711 | ❌ | ✅ | ❌ | ⬜ | 1 |
| reflex-dev__reflex-4717 | ✅ | ✅ | ❌ | ✅ | 3 |
| reflex-dev__reflex-4720 | ❌ | ✅ | ❌ | ❌ | 1 |
| reflex-dev__reflex-5039 | ✅ | ✅ | ⚠️ | ⬜ | 2 |
| run-llama__llama_deploy-330 | ✅ | ✅ | ✅ | ✅ | 4 |
| run-llama__llama_deploy-356 | ✅ | ✅ | ✅ | ✅ | 4 |
| run-llama__llama_deploy-372 | ✅ | ✅ | ⬜ | ✅ | 3 |
| run-llama__llama_deploy-384 | ✅ | ✅ | ✅ | ✅ | 4 |
| run-llama__llama_deploy-397 | ✅ | ✅ | ❌ | ✅ | 3 |
| run-llama__llama_deploy-399 | ✅ | ✅ | ❌ | ✅ | 3 |
| run-llama__llama_deploy-438 | ✅ | ✅ | ❌ | ✅ | 3 |
| run-llama__llama_deploy-458 | ❌ | ✅ | ⬜ | ✅ | 2 |
| scrapy-plugins__scrapy-splash-324 | ✅ | ✅ | ❌ | ⬜ | 2 |
| shapely__shapely-2224 | ✅ | ✅ | ✅ | ✅ | 4 |
| shapely__shapely-2226 | ✅ | ✅ | ✅ | ✅ | 4 |
| shapely__shapely-2255 | ✅ | ✅ | ⬜ | ✅ | 3 |
| sissbruecker__linkding-971 | ✅ | ✅ | ❌ | ✅ | 3 |
| sissbruecker__linkding-984 | ✅ | ✅ | ❌ | ✅ | 3 |
| sissbruecker__linkding-989 | ✅ | ✅ | ✅ | ✅ | 4 |
| sissbruecker__linkding-995 | ❌ | ✅ | ✅ | ❌ | 2 |
| sissbruecker__linkding-999 | ✅ | ✅ | ❌ | ✅ | 3 |
| sphinx-doc__sphinx-12975 | ✅ | ❌ | ❌ | ✅ | 2 |
| sphinx-doc__sphinx-13127 | ✅ | ✅ | ✅ | ✅ | 4 |
| sphinx-doc__sphinx-13200 | ✅ | ✅ | ❌ | ✅ | 3 |
| sphinx-doc__sphinx-13253 | ✅ | ✅ | ✅ | ✅ | 4 |
| sphinx-doc__sphinx-13261 | ✅ | ✅ | ❌ | ✅ | 3 |
| sphinx-doc__sphinx-13318 | ✅ | ✅ | ❌ | ✅ | 3 |
| stanford-crfm__helm-3467 | ❌ | ✅ | ❌ | ✅ | 2 |
| stanfordnlp__dspy-1609 | ❌ | ✅ | ✅ | ❌ | 2 |
| stanfordnlp__dspy-1651 | ✅ | ✅ | ✅ | ✅ | 4 |
| stanfordnlp__dspy-1741 | ❌ | ❌ | ✅ | ❌ | 1 |
| stanfordnlp__dspy-1801 | ✅ | ✅ | ❌ | ⬜ | 2 |
| streamlink__streamlink-6242 | ✅ | ✅ | ✅ | ✅ | 4 |
| streamlink__streamlink-6328 | ❌ | ✅ | ✅ | ❌ | 2 |
| streamlink__streamlink-6338 | ✅ | ✅ | ❌ | ✅ | 3 |
| streamlink__streamlink-6361 | ✅ | ✅ | ✅ | ✅ | 4 |
| streamlink__streamlink-6381 | ✅ | ✅ | ✅ | ❌ | 3 |
| streamlink__streamlink-6389 | ✅ | ✅ | ✅ | ❌ | 3 |
| streamlink__streamlink-6439 | ✅ | ✅ | ✅ | ✅ | 4 |
| sympy__sympy-27462 | ✅ | ✅ | ✅ | ✅ | 4 |
| theoehrly__fast-f1-699 | ❌ | ✅ | ✅ | ✅ | 3 |
| tox-dev__tox-3388 | ❌ | ✅ | ❌ | ❌ | 1 |
| tox-dev__tox-3409 | ❌ | ✅ | ✅ | ❌ | 2 |
| urllib3__urllib3-3527 | ❌ | ❌ | ❌ | ❌ | 0 |
| wemake-services__wemake-python-styleguide-3114 | ❌ | ✅ | ✅ | ✅ | 3 |
| wemake-services__wemake-python-styleguide-3117 | ✅ | ✅ | ✅ | ✅ | 4 |
| wemake-services__wemake-python-styleguide-3128 | ❌ | ✅ | ❌ | ✅ | 2 |
| wemake-services__wemake-python-styleguide-3129 | ✅ | ❌ | ✅ | ✅ | 3 |
| wemake-services__wemake-python-styleguide-3195 | ❌ | ❌ | ✅ | ⬜ | 1 |
| wireservice__csvkit-1274 | ✅ | ✅ | ✅ | ✅ | 4 |
| wireservice__csvkit-1281 | ✅ | ✅ | ✅ | ✅ | 4 |
| yt-dlp__yt-dlp-11425 | ✅ | ✅ | ✅ | ✅ | 4 |
| yt-dlp__yt-dlp-11880 | ✅ | ✅ | ✅ | ✅ | 4 |
| yt-dlp__yt-dlp-12684 | ✅ | ✅ | ❌ | ✅ | 3 |
| yt-dlp__yt-dlp-12714 | ✅ | ✅ | ✅ | ✅ | 4 |

## 2. Trajectory per task

Cell = trajectory format (`folder` = one folder per task, otherwise the file type); empty = no trajectory.

| instance_id | tianxicode_deepseek-flash | sapient-slingshot-agent_v3.4.0_gpt-5.6-sol | ami-agent | agav_gpt-5.5 | with trajectory |
|---|---|---|---|---|---|
| **with trajectory** | **300/300** | **14/300** | **290/300** | **3/300** |  |
| aiogram__aiogram-1594 | folder |  | json |  | 2 |
| amoffat__sh-744 | folder |  | json |  | 2 |
| arviz-devs__arviz-2413 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3749 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3764 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3767 | folder | md | json |  | 3 |
| aws-cloudformation__cfn-lint-3768 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3770 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3779 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3789 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3798 | folder | md | json |  | 3 |
| aws-cloudformation__cfn-lint-3805 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3817 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3821 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3854 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3855 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3856 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3862 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3866 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3875 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3890 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3947 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-3982 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-4002 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-4009 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-4016 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-4023 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-4032 | folder |  | json |  | 2 |
| aws-cloudformation__cfn-lint-4051 | folder |  | json |  | 2 |
| beancount__beancount-931 | folder |  | json |  | 2 |
| beetbox__beets-5457 | folder |  | json |  | 2 |
| beetbox__beets-5495 | folder |  | json |  | 2 |
| beetbox__beets-5682 | folder |  | json |  | 2 |
| beeware__briefcase-2075 | folder |  | json |  | 2 |
| beeware__briefcase-2085 | folder |  | json |  | 2 |
| beeware__briefcase-2088 | folder |  | json |  | 2 |
| beeware__briefcase-2214 | folder |  | json |  | 2 |
| bridgecrewio__checkov-6893 | folder |  | json |  | 2 |
| bridgecrewio__checkov-6895 | folder |  | json |  | 2 |
| bridgecrewio__checkov-7002 | folder |  | json |  | 2 |
| conan-io__conan-17092 | folder |  | json |  | 2 |
| conan-io__conan-17102 | folder |  | json |  | 2 |
| conan-io__conan-17117 | folder |  | json |  | 2 |
| conan-io__conan-17123 | folder |  | json |  | 2 |
| conan-io__conan-17129 | folder |  | json |  | 2 |
| conan-io__conan-17132 | folder |  | json |  | 2 |
| conan-io__conan-17183 | folder |  | json |  | 2 |
| conan-io__conan-17266 | folder |  | json |  | 2 |
| conan-io__conan-17292 | folder |  | json |  | 2 |
| conan-io__conan-17300 | folder |  | json |  | 2 |
| conan-io__conan-17301 | folder |  | json |  | 2 |
| conan-io__conan-17302 | folder |  | json |  | 2 |
| conan-io__conan-17326 | folder |  |  |  | 1 |
| conan-io__conan-17366 | folder |  | json |  | 2 |
| conan-io__conan-17382 | folder |  | json |  | 2 |
| conan-io__conan-17408 | folder |  | json |  | 2 |
| conan-io__conan-17514 | folder |  | json |  | 2 |
| conan-io__conan-17517 | folder |  | json |  | 2 |
| conan-io__conan-17520 | folder |  | json |  | 2 |
| conan-io__conan-17532 | folder |  | json |  | 2 |
| conan-io__conan-17538 | folder |  | json |  | 2 |
| conan-io__conan-17708 | folder |  | json |  | 2 |
| conan-io__conan-17725 | folder |  | json |  | 2 |
| conan-io__conan-17781 | folder |  | json |  | 2 |
| conan-io__conan-17819 | folder |  | json |  | 2 |
| conan-io__conan-17917 | folder |  | json |  | 2 |
| conan-io__conan-17923 | folder |  | json |  | 2 |
| conan-io__conan-17967 | folder |  | json |  | 2 |
| conan-io__conan-18028 | folder |  | json |  | 2 |
| conan-io__conan-18037 | folder |  | json |  | 2 |
| cyclotruc__gitingest-115 | folder |  | json |  | 2 |
| cyclotruc__gitingest-134 | folder |  | json |  | 2 |
| cyclotruc__gitingest-94 | folder |  | json |  | 2 |
| deepset-ai__haystack-8489 | folder | md | json |  | 3 |
| deepset-ai__haystack-8525 | folder | md | json |  | 3 |
| deepset-ai__haystack-8609 | folder |  | json |  | 2 |
| deepset-ai__haystack-8619 | folder |  | json |  | 2 |
| deepset-ai__haystack-8725 | folder |  | json |  | 2 |
| deepset-ai__haystack-8799 | folder |  | json |  | 2 |
| deepset-ai__haystack-8879 | folder |  | json |  | 2 |
| deepset-ai__haystack-8940 | folder |  |  |  | 1 |
| deepset-ai__haystack-8969 | folder |  | json |  | 2 |
| deepset-ai__haystack-8973 | folder |  | json |  | 2 |
| deepset-ai__haystack-8981 | folder |  | json |  | 2 |
| deepset-ai__haystack-8992 | folder |  | json |  | 2 |
| deepset-ai__haystack-8993 | folder |  | json |  | 2 |
| deepset-ai__haystack-8997 | folder |  | json |  | 2 |
| deepset-ai__haystack-9027 | folder |  | json |  | 2 |
| deepset-ai__haystack-9066 | folder |  | json |  | 2 |
| delgan__loguru-1297 | folder |  | json |  | 2 |
| delgan__loguru-1306 | folder |  | json |  | 2 |
| dynaconf__dynaconf-1225 | folder |  | json |  | 2 |
| dynaconf__dynaconf-1238 | folder |  | json |  | 2 |
| dynaconf__dynaconf-1241 | folder |  | json |  | 2 |
| dynaconf__dynaconf-1249 | folder |  | json |  | 2 |
| encode__starlette-2812 | folder |  | json |  | 2 |
| facebookresearch__hydra-3005 | folder |  | json |  | 2 |
| falconry__falcon-2366 | folder |  | json |  | 2 |
| falconry__falcon-2419 | folder |  | json |  | 2 |
| feast-dev__feast-5036 | folder |  | json |  | 2 |
| flexget__flexget-4244 | folder |  | json |  | 2 |
| flexget__flexget-4306 | folder |  | json |  | 2 |
| fonttools__fonttools-3682 | folder |  | json |  | 2 |
| fonttools__fonttools-3726 | folder |  | json |  | 2 |
| geopandas__geopandas-3471 | folder |  | json |  | 2 |
| hiyouga__llama-factory-7505 | folder |  |  |  | 1 |
| huggingface__smolagents-285 | folder |  | json |  | 2 |
| huggingface__smolagents-405 | folder |  | json |  | 2 |
| huggingface__smolagents-731 | folder |  | json |  | 2 |
| huggingface__smolagents-843 | folder |  | json |  | 2 |
| icloud-photos-downloader__icloud_photos_downloader-1060 | folder |  | json |  | 2 |
| instructlab__instructlab-2526 | folder |  | json |  | 2 |
| instructlab__instructlab-2540 | folder |  | json |  | 2 |
| instructlab__instructlab-2548 | folder |  | json |  | 2 |
| instructlab__instructlab-2572 | folder |  | json |  | 2 |
| instructlab__instructlab-2585 | folder | md | json |  | 3 |
| instructlab__instructlab-2592 | folder |  | json |  | 2 |
| instructlab__instructlab-2825 | folder |  | json |  | 2 |
| instructlab__instructlab-2886 | folder |  | json |  | 2 |
| instructlab__instructlab-2927 | folder |  | json |  | 2 |
| instructlab__instructlab-3060 | folder |  | json |  | 2 |
| instructlab__instructlab-3118 | folder |  | json |  | 2 |
| ipython__ipython-14695 | folder |  | json |  | 2 |
| ipython__ipython-14798 | folder |  | json |  | 2 |
| ipython__ipython-14822 | folder |  | json |  | 2 |
| ipython__ipython-14838 | folder |  | json |  | 2 |
| iterative__dvc-10711 | folder |  | json |  | 2 |
| jazzband__tablib-613 | folder |  | json |  | 2 |
| joke2k__faker-2142 | folder |  | json |  | 2 |
| joke2k__faker-2155 | folder |  | json |  | 2 |
| joke2k__faker-2162 | folder |  | json |  | 2 |
| joke2k__faker-2173 | folder |  | json |  | 2 |
| joke2k__faker-2190 | folder |  | json |  | 2 |
| jupyterlab__jupyter-ai-1022 | folder |  | json |  | 2 |
| jupyterlab__jupyter-ai-1125 | folder |  |  |  | 1 |
| jupyterlab__jupyter-ai-1294 | folder |  | json |  | 2 |
| kedro-org__kedro-4387 | folder |  | json |  | 2 |
| kedro-org__kedro-4406 | folder |  | json |  | 2 |
| kedro-org__kedro-4408 | folder |  | json |  | 2 |
| kedro-org__kedro-4427 | folder |  | json |  | 2 |
| kedro-org__kedro-4580 | folder |  | json |  | 2 |
| keras-team__keras-20389 | folder | md | json |  | 3 |
| keras-team__keras-20396 | folder |  | json |  | 2 |
| keras-team__keras-20443 | folder |  | json |  | 2 |
| keras-team__keras-20534 | folder |  | json |  | 2 |
| keras-team__keras-20609 | folder |  | json |  | 2 |
| keras-team__keras-20880 | folder |  | json |  | 2 |
| keras-team__keras-21072 | folder |  | json |  | 2 |
| koxudaxi__datamodel-code-generator-2259 | folder |  | json |  | 2 |
| koxudaxi__datamodel-code-generator-2327 | folder |  |  |  | 1 |
| koxudaxi__datamodel-code-generator-2349 | folder |  | json |  | 2 |
| kozea__weasyprint-2300 | folder |  | json |  | 2 |
| kozea__weasyprint-2303 | folder |  | json |  | 2 |
| kozea__weasyprint-2387 | folder |  | json |  | 2 |
| kozea__weasyprint-2398 | folder |  | json |  | 2 |
| kozea__weasyprint-2405 | folder |  | json |  | 2 |
| kubernetes-client__python-2303 | folder |  | json |  | 2 |
| matplotlib__matplotlib-28933 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29007 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29249 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29258 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29285 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29388 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29431 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29486 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29537 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29689 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29721 | folder |  | json |  | 2 |
| matplotlib__matplotlib-29781 | folder |  | json |  | 2 |
| mikedh__trimesh-2354 | folder |  | json |  | 2 |
| mikedh__trimesh-2363 | folder |  | json |  | 2 |
| modelcontextprotocol__python-sdk-167 | folder |  | json |  | 2 |
| modelcontextprotocol__python-sdk-222 | folder |  | json |  | 2 |
| pallets__flask-5626 | folder |  | json |  | 2 |
| pallets__flask-5637 | folder |  | json |  | 2 |
| patroni__patroni-3198 | folder |  | json |  | 2 |
| pdm-project__pdm-3237 | folder |  | json |  | 2 |
| pdm-project__pdm-3250 | folder |  | json |  | 2 |
| pdm-project__pdm-3255 | folder |  | json |  | 2 |
| pdm-project__pdm-3314 | folder |  | json |  | 2 |
| pdm-project__pdm-3374 | folder |  | json |  | 2 |
| pdm-project__pdm-3419 | folder |  | json |  | 2 |
| pdm-project__pdm-3420 | folder |  | json |  | 2 |
| privacyidea__privacyidea-4206 | folder |  | json |  | 2 |
| privacyidea__privacyidea-4223 | folder |  | json |  | 2 |
| privacyidea__privacyidea-4226 | folder |  | json |  | 2 |
| privacyidea__privacyidea-4233 | folder |  | json |  | 2 |
| privacyidea__privacyidea-4251 | folder |  | json |  | 2 |
| projectmesa__mesa-2394 | folder | md | json |  | 3 |
| projectmesa__mesa-2418 | folder |  | json |  | 2 |
| projectmesa__mesa-2523 | folder |  | json |  | 2 |
| projectmesa__mesa-2605 | folder |  | json |  | 2 |
| projectmesa__mesa-2632 | folder |  | json |  | 2 |
| pvlib__pvlib-python-2249 | folder | md | json |  | 3 |
| pvlib__pvlib-python-2286 | folder |  | json | txt | 3 |
| pvlib__pvlib-python-2291 | folder |  | json |  | 2 |
| pvlib__pvlib-python-2292 | folder |  | json |  | 2 |
| pvlib__pvlib-python-2341 | folder |  | json |  | 2 |
| pvlib__pvlib-python-2393 | folder |  | json |  | 2 |
| pvlib__pvlib-python-2400 | folder |  | json |  | 2 |
| pybamm-team__pybamm-4644 | folder |  | json |  | 2 |
| pybamm-team__pybamm-4816 | folder |  | json |  | 2 |
| pybamm-team__pybamm-4865 | folder |  | json |  | 2 |
| pydata__xarray-10076 | folder |  | json |  | 2 |
| pydata__xarray-9586 | folder | md |  |  | 2 |
| pydata__xarray-9636 | folder |  | json |  | 2 |
| pydata__xarray-9760 | folder |  | json |  | 2 |
| pydata__xarray-9765 | folder |  | json |  | 2 |
| pydata__xarray-9971 | folder |  | json |  | 2 |
| pydata__xarray-9974 | folder |  | json |  | 2 |
| pylint-dev__pylint-10044 | folder |  | json |  | 2 |
| pylint-dev__pylint-10062 | folder |  | json |  | 2 |
| pylint-dev__pylint-10089 | folder |  | json |  | 2 |
| pylint-dev__pylint-10097 | folder | md | json |  | 3 |
| pylint-dev__pylint-10240 | folder |  | json |  | 2 |
| pypa__twine-1225 | folder |  | json |  | 2 |
| pypsa__pypsa-1091 | folder | md |  |  | 2 |
| pypsa__pypsa-1112 | folder |  | json |  | 2 |
| pypsa__pypsa-1172 | folder |  | json |  | 2 |
| pypsa__pypsa-1195 | folder |  | json |  | 2 |
| python-babel__babel-1141 | folder | md | json | txt | 4 |
| python-babel__babel-1163 | folder |  | json |  | 2 |
| python-babel__babel-1164 | folder |  | json |  | 2 |
| python-babel__babel-1179 | folder |  | json |  | 2 |
| python-babel__babel-1194 | folder |  | json |  | 2 |
| python-control__python-control-1064 | folder |  | json |  | 2 |
| python-control__python-control-1111 | folder |  | json |  | 2 |
| python-control__python-control-1142 | folder |  | json |  | 2 |
| python-telegram-bot__python-telegram-bot-4617 | folder |  | json |  | 2 |
| python-telegram-bot__python-telegram-bot-4626 | folder |  | json |  | 2 |
| python-telegram-bot__python-telegram-bot-4673 | folder |  | json |  | 2 |
| pytorch__torchtune-1806 | folder | md | json |  | 3 |
| pytorch__torchtune-2066 | folder |  | json |  | 2 |
| pytorch__torchtune-2139 | folder |  | json |  | 2 |
| qtile__qtile-5154 | folder |  | json |  | 2 |
| reata__sqllineage-661 | folder |  | json |  | 2 |
| reata__sqllineage-694 | folder |  | json |  | 2 |
| reflex-dev__reflex-4087 | folder |  | json |  | 2 |
| reflex-dev__reflex-4129 | folder | md | json |  | 3 |
| reflex-dev__reflex-4266 | folder |  | json |  | 2 |
| reflex-dev__reflex-4347 | folder |  | json |  | 2 |
| reflex-dev__reflex-4371 | folder |  |  |  | 1 |
| reflex-dev__reflex-4427 | folder |  | json |  | 2 |
| reflex-dev__reflex-4510 | folder |  | json |  | 2 |
| reflex-dev__reflex-4563 | folder |  | json |  | 2 |
| reflex-dev__reflex-4711 | folder |  | json |  | 2 |
| reflex-dev__reflex-4717 | folder |  | json |  | 2 |
| reflex-dev__reflex-4720 | folder |  | json |  | 2 |
| reflex-dev__reflex-5039 | folder |  |  |  | 1 |
| run-llama__llama_deploy-330 | folder |  | json |  | 2 |
| run-llama__llama_deploy-356 | folder |  | json |  | 2 |
| run-llama__llama_deploy-372 | folder |  | json |  | 2 |
| run-llama__llama_deploy-384 | folder |  | json |  | 2 |
| run-llama__llama_deploy-397 | folder |  | json |  | 2 |
| run-llama__llama_deploy-399 | folder |  | json |  | 2 |
| run-llama__llama_deploy-438 | folder |  | json |  | 2 |
| run-llama__llama_deploy-458 | folder |  | json |  | 2 |
| scrapy-plugins__scrapy-splash-324 | folder |  | json |  | 2 |
| shapely__shapely-2224 | folder |  | json |  | 2 |
| shapely__shapely-2226 | folder |  | json |  | 2 |
| shapely__shapely-2255 | folder |  |  |  | 1 |
| sissbruecker__linkding-971 | folder |  | json |  | 2 |
| sissbruecker__linkding-984 | folder |  | json |  | 2 |
| sissbruecker__linkding-989 | folder |  | json |  | 2 |
| sissbruecker__linkding-995 | folder |  | json |  | 2 |
| sissbruecker__linkding-999 | folder |  | json |  | 2 |
| sphinx-doc__sphinx-12975 | folder |  | json |  | 2 |
| sphinx-doc__sphinx-13127 | folder |  | json |  | 2 |
| sphinx-doc__sphinx-13200 | folder |  | json |  | 2 |
| sphinx-doc__sphinx-13253 | folder |  | json |  | 2 |
| sphinx-doc__sphinx-13261 | folder |  | json |  | 2 |
| sphinx-doc__sphinx-13318 | folder |  | json |  | 2 |
| stanford-crfm__helm-3467 | folder |  | json |  | 2 |
| stanfordnlp__dspy-1609 | folder |  | json |  | 2 |
| stanfordnlp__dspy-1651 | folder |  | json |  | 2 |
| stanfordnlp__dspy-1741 | folder |  | json |  | 2 |
| stanfordnlp__dspy-1801 | folder |  | json |  | 2 |
| streamlink__streamlink-6242 | folder |  | json | txt | 3 |
| streamlink__streamlink-6328 | folder |  | json |  | 2 |
| streamlink__streamlink-6338 | folder |  | json |  | 2 |
| streamlink__streamlink-6361 | folder |  | json |  | 2 |
| streamlink__streamlink-6381 | folder |  | json |  | 2 |
| streamlink__streamlink-6389 | folder |  | json |  | 2 |
| streamlink__streamlink-6439 | folder |  | json |  | 2 |
| sympy__sympy-27462 | folder |  | json |  | 2 |
| theoehrly__fast-f1-699 | folder |  | json |  | 2 |
| tox-dev__tox-3388 | folder |  | json |  | 2 |
| tox-dev__tox-3409 | folder |  | json |  | 2 |
| urllib3__urllib3-3527 | folder |  | json |  | 2 |
| wemake-services__wemake-python-styleguide-3114 | folder |  | json |  | 2 |
| wemake-services__wemake-python-styleguide-3117 | folder |  | json |  | 2 |
| wemake-services__wemake-python-styleguide-3128 | folder |  | json |  | 2 |
| wemake-services__wemake-python-styleguide-3129 | folder |  | json |  | 2 |
| wemake-services__wemake-python-styleguide-3195 | folder |  | json |  | 2 |
| wireservice__csvkit-1274 | folder |  | json |  | 2 |
| wireservice__csvkit-1281 | folder |  | json |  | 2 |
| yt-dlp__yt-dlp-11425 | folder |  | json |  | 2 |
| yt-dlp__yt-dlp-11880 | folder |  | json |  | 2 |
| yt-dlp__yt-dlp-12684 | folder |  | json |  | 2 |
| yt-dlp__yt-dlp-12714 | folder |  | json |  | 2 |

## 3. Resolved by all submissions (102 tasks)

Cells show each submission's outcome; `with trajectory` = number of submissions with a trajectory for the task.

| # | instance_id | tianxicode_deepseek-flash | sapient-slingshot-agent_v3.4.0_gpt-5.6-sol | ami-agent | agav_gpt-5.5 | with trajectory |
|---|---|---|---|---|---|---|
| 1 | beancount__beancount-931 | ✅ | ✅ | ✅ | ✅ | 2 |
| 2 | beetbox__beets-5457 | ✅ | ✅ | ✅ | ✅ | 2 |
| 3 | beetbox__beets-5495 | ✅ | ✅ | ✅ | ✅ | 2 |
| 4 | beeware__briefcase-2085 | ✅ | ✅ | ✅ | ✅ | 2 |
| 5 | conan-io__conan-17102 | ✅ | ✅ | ✅ | ✅ | 2 |
| 6 | conan-io__conan-17117 | ✅ | ✅ | ✅ | ✅ | 2 |
| 7 | conan-io__conan-17123 | ✅ | ✅ | ✅ | ✅ | 2 |
| 8 | conan-io__conan-17129 | ✅ | ✅ | ✅ | ✅ | 2 |
| 9 | conan-io__conan-17183 | ✅ | ✅ | ✅ | ✅ | 2 |
| 10 | conan-io__conan-17266 | ✅ | ✅ | ✅ | ✅ | 2 |
| 11 | conan-io__conan-17292 | ✅ | ✅ | ✅ | ✅ | 2 |
| 12 | conan-io__conan-17300 | ✅ | ✅ | ✅ | ✅ | 2 |
| 13 | conan-io__conan-17301 | ✅ | ✅ | ✅ | ✅ | 2 |
| 14 | conan-io__conan-17302 | ✅ | ✅ | ✅ | ✅ | 2 |
| 15 | conan-io__conan-17326 | ✅ | ✅ | ✅ | ✅ | 1 |
| 16 | conan-io__conan-17382 | ✅ | ✅ | ✅ | ✅ | 2 |
| 17 | conan-io__conan-17408 | ✅ | ✅ | ✅ | ✅ | 2 |
| 18 | conan-io__conan-17517 | ✅ | ✅ | ✅ | ✅ | 2 |
| 19 | conan-io__conan-17520 | ✅ | ✅ | ✅ | ✅ | 2 |
| 20 | conan-io__conan-17532 | ✅ | ✅ | ✅ | ✅ | 2 |
| 21 | conan-io__conan-17917 | ✅ | ✅ | ✅ | ✅ | 2 |
| 22 | conan-io__conan-17923 | ✅ | ✅ | ✅ | ✅ | 2 |
| 23 | conan-io__conan-18028 | ✅ | ✅ | ✅ | ✅ | 2 |
| 24 | conan-io__conan-18037 | ✅ | ✅ | ✅ | ✅ | 2 |
| 25 | cyclotruc__gitingest-94 | ✅ | ✅ | ✅ | ✅ | 2 |
| 26 | deepset-ai__haystack-8609 | ✅ | ✅ | ✅ | ✅ | 2 |
| 27 | deepset-ai__haystack-8725 | ✅ | ✅ | ✅ | ✅ | 2 |
| 28 | deepset-ai__haystack-8799 | ✅ | ✅ | ✅ | ✅ | 2 |
| 29 | deepset-ai__haystack-8969 | ✅ | ✅ | ✅ | ✅ | 2 |
| 30 | deepset-ai__haystack-8973 | ✅ | ✅ | ✅ | ✅ | 2 |
| 31 | deepset-ai__haystack-8992 | ✅ | ✅ | ✅ | ✅ | 2 |
| 32 | deepset-ai__haystack-8997 | ✅ | ✅ | ✅ | ✅ | 2 |
| 33 | delgan__loguru-1297 | ✅ | ✅ | ✅ | ✅ | 2 |
| 34 | delgan__loguru-1306 | ✅ | ✅ | ✅ | ✅ | 2 |
| 35 | dynaconf__dynaconf-1225 | ✅ | ✅ | ✅ | ✅ | 2 |
| 36 | dynaconf__dynaconf-1241 | ✅ | ✅ | ✅ | ✅ | 2 |
| 37 | feast-dev__feast-5036 | ✅ | ✅ | ✅ | ✅ | 2 |
| 38 | flexget__flexget-4244 | ✅ | ✅ | ✅ | ✅ | 2 |
| 39 | fonttools__fonttools-3682 | ✅ | ✅ | ✅ | ✅ | 2 |
| 40 | icloud-photos-downloader__icloud_photos_downloader-1060 | ✅ | ✅ | ✅ | ✅ | 2 |
| 41 | instructlab__instructlab-2548 | ✅ | ✅ | ✅ | ✅ | 2 |
| 42 | ipython__ipython-14695 | ✅ | ✅ | ✅ | ✅ | 2 |
| 43 | ipython__ipython-14822 | ✅ | ✅ | ✅ | ✅ | 2 |
| 44 | ipython__ipython-14838 | ✅ | ✅ | ✅ | ✅ | 2 |
| 45 | iterative__dvc-10711 | ✅ | ✅ | ✅ | ✅ | 2 |
| 46 | joke2k__faker-2155 | ✅ | ✅ | ✅ | ✅ | 2 |
| 47 | joke2k__faker-2173 | ✅ | ✅ | ✅ | ✅ | 2 |
| 48 | joke2k__faker-2190 | ✅ | ✅ | ✅ | ✅ | 2 |
| 49 | jupyterlab__jupyter-ai-1294 | ✅ | ✅ | ✅ | ✅ | 2 |
| 50 | koxudaxi__datamodel-code-generator-2259 | ✅ | ✅ | ✅ | ✅ | 2 |
| 51 | koxudaxi__datamodel-code-generator-2349 | ✅ | ✅ | ✅ | ✅ | 2 |
| 52 | kozea__weasyprint-2300 | ✅ | ✅ | ✅ | ✅ | 2 |
| 53 | kozea__weasyprint-2303 | ✅ | ✅ | ✅ | ✅ | 2 |
| 54 | kozea__weasyprint-2398 | ✅ | ✅ | ✅ | ✅ | 2 |
| 55 | kozea__weasyprint-2405 | ✅ | ✅ | ✅ | ✅ | 2 |
| 56 | pallets__flask-5626 | ✅ | ✅ | ✅ | ✅ | 2 |
| 57 | pallets__flask-5637 | ✅ | ✅ | ✅ | ✅ | 2 |
| 58 | patroni__patroni-3198 | ✅ | ✅ | ✅ | ✅ | 2 |
| 59 | pdm-project__pdm-3255 | ✅ | ✅ | ✅ | ✅ | 2 |
| 60 | pdm-project__pdm-3420 | ✅ | ✅ | ✅ | ✅ | 2 |
| 61 | projectmesa__mesa-2394 | ✅ | ✅ | ✅ | ✅ | 3 |
| 62 | projectmesa__mesa-2418 | ✅ | ✅ | ✅ | ✅ | 2 |
| 63 | projectmesa__mesa-2632 | ✅ | ✅ | ✅ | ✅ | 2 |
| 64 | pvlib__pvlib-python-2249 | ✅ | ✅ | ✅ | ✅ | 3 |
| 65 | pvlib__pvlib-python-2286 | ✅ | ✅ | ✅ | ✅ | 3 |
| 66 | pvlib__pvlib-python-2291 | ✅ | ✅ | ✅ | ✅ | 2 |
| 67 | pvlib__pvlib-python-2341 | ✅ | ✅ | ✅ | ✅ | 2 |
| 68 | pvlib__pvlib-python-2393 | ✅ | ✅ | ✅ | ✅ | 2 |
| 69 | pvlib__pvlib-python-2400 | ✅ | ✅ | ✅ | ✅ | 2 |
| 70 | pybamm-team__pybamm-4644 | ✅ | ✅ | ✅ | ✅ | 2 |
| 71 | pybamm-team__pybamm-4865 | ✅ | ✅ | ✅ | ✅ | 2 |
| 72 | pydata__xarray-9974 | ✅ | ✅ | ✅ | ✅ | 2 |
| 73 | pylint-dev__pylint-10089 | ✅ | ✅ | ✅ | ✅ | 2 |
| 74 | pypa__twine-1225 | ✅ | ✅ | ✅ | ✅ | 2 |
| 75 | python-babel__babel-1141 | ✅ | ✅ | ✅ | ✅ | 4 |
| 76 | python-babel__babel-1163 | ✅ | ✅ | ✅ | ✅ | 2 |
| 77 | python-babel__babel-1179 | ✅ | ✅ | ✅ | ✅ | 2 |
| 78 | python-babel__babel-1194 | ✅ | ✅ | ✅ | ✅ | 2 |
| 79 | python-control__python-control-1111 | ✅ | ✅ | ✅ | ✅ | 2 |
| 80 | pytorch__torchtune-1806 | ✅ | ✅ | ✅ | ✅ | 3 |
| 81 | reflex-dev__reflex-4087 | ✅ | ✅ | ✅ | ✅ | 2 |
| 82 | reflex-dev__reflex-4266 | ✅ | ✅ | ✅ | ✅ | 2 |
| 83 | reflex-dev__reflex-4510 | ✅ | ✅ | ✅ | ✅ | 2 |
| 84 | run-llama__llama_deploy-330 | ✅ | ✅ | ✅ | ✅ | 2 |
| 85 | run-llama__llama_deploy-356 | ✅ | ✅ | ✅ | ✅ | 2 |
| 86 | run-llama__llama_deploy-384 | ✅ | ✅ | ✅ | ✅ | 2 |
| 87 | shapely__shapely-2224 | ✅ | ✅ | ✅ | ✅ | 2 |
| 88 | shapely__shapely-2226 | ✅ | ✅ | ✅ | ✅ | 2 |
| 89 | sissbruecker__linkding-989 | ✅ | ✅ | ✅ | ✅ | 2 |
| 90 | sphinx-doc__sphinx-13127 | ✅ | ✅ | ✅ | ✅ | 2 |
| 91 | sphinx-doc__sphinx-13253 | ✅ | ✅ | ✅ | ✅ | 2 |
| 92 | stanfordnlp__dspy-1651 | ✅ | ✅ | ✅ | ✅ | 2 |
| 93 | streamlink__streamlink-6242 | ✅ | ✅ | ✅ | ✅ | 3 |
| 94 | streamlink__streamlink-6361 | ✅ | ✅ | ✅ | ✅ | 2 |
| 95 | streamlink__streamlink-6439 | ✅ | ✅ | ✅ | ✅ | 2 |
| 96 | sympy__sympy-27462 | ✅ | ✅ | ✅ | ✅ | 2 |
| 97 | wemake-services__wemake-python-styleguide-3117 | ✅ | ✅ | ✅ | ✅ | 2 |
| 98 | wireservice__csvkit-1274 | ✅ | ✅ | ✅ | ✅ | 2 |
| 99 | wireservice__csvkit-1281 | ✅ | ✅ | ✅ | ✅ | 2 |
| 100 | yt-dlp__yt-dlp-11425 | ✅ | ✅ | ✅ | ✅ | 2 |
| 101 | yt-dlp__yt-dlp-11880 | ✅ | ✅ | ✅ | ✅ | 2 |
| 102 | yt-dlp__yt-dlp-12714 | ✅ | ✅ | ✅ | ✅ | 2 |

## 4. Resolved by none (13 tasks)

Cells show each submission's outcome; `with trajectory` = number of submissions with a trajectory for the task.

| # | instance_id | tianxicode_deepseek-flash | sapient-slingshot-agent_v3.4.0_gpt-5.6-sol | ami-agent | agav_gpt-5.5 | with trajectory |
|---|---|---|---|---|---|---|
| 1 | aws-cloudformation__cfn-lint-3798 | ❌ | ❌ | ❌ | ❌ | 3 |
| 2 | aws-cloudformation__cfn-lint-3855 | ❌ | ❌ | ❌ | ❌ | 2 |
| 3 | aws-cloudformation__cfn-lint-3866 | ❌ | ❌ | ❌ | ❌ | 2 |
| 4 | bridgecrewio__checkov-6895 | ❌ | ❌ | ❌ | ❌ | 2 |
| 5 | cyclotruc__gitingest-134 | ❌ | ❌ | ❌ | ❌ | 2 |
| 6 | huggingface__smolagents-731 | ❌ | ❌ | ❌ | ❌ | 2 |
| 7 | joke2k__faker-2142 | ❌ | ❌ | ❌ | ❌ | 2 |
| 8 | kedro-org__kedro-4580 | ❌ | ❌ | ❌ | ❌ | 2 |
| 9 | matplotlib__matplotlib-29781 | ❌ | ❌ | ❌ | ❌ | 2 |
| 10 | pypsa__pypsa-1195 | ❌ | ❌ | ❌ | ❌ | 2 |
| 11 | python-telegram-bot__python-telegram-bot-4617 | ❌ | ❌ | ❌ | ❌ | 2 |
| 12 | python-telegram-bot__python-telegram-bot-4673 | ❌ | ❌ | ❌ | ❌ | 2 |
| 13 | urllib3__urllib3-3527 | ❌ | ❌ | ❌ | ❌ | 2 |

## 5. tianxicode_deepseek-flash vs ami-agent

Cells show each submission's outcome; `with trajectory` = number of submissions with a trajectory for the task. Not resolved = failed, empty patch or error.

### 5a. Resolved by tianxicode_deepseek-flash, not by ami-agent (80 tasks)

| # | instance_id | tianxicode_deepseek-flash | sapient-slingshot-agent_v3.4.0_gpt-5.6-sol | ami-agent | agav_gpt-5.5 | with trajectory |
|---|---|---|---|---|---|---|
| 1 | aiogram__aiogram-1594 | ✅ | ✅ | ❌ | ✅ | 2 |
| 2 | arviz-devs__arviz-2413 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 3 | aws-cloudformation__cfn-lint-3749 | ✅ | ✅ | ❌ | ✅ | 2 |
| 4 | beetbox__beets-5682 | ✅ | ✅ | ❌ | ❌ | 2 |
| 5 | conan-io__conan-17092 | ✅ | ✅ | ❌ | ✅ | 2 |
| 6 | conan-io__conan-17132 | ✅ | ❌ | ❌ | ✅ | 2 |
| 7 | conan-io__conan-17366 | ✅ | ✅ | ❌ | ✅ | 2 |
| 8 | conan-io__conan-17514 | ✅ | ❌ | ❌ | ✅ | 2 |
| 9 | conan-io__conan-17708 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 10 | conan-io__conan-17725 | ✅ | ✅ | ❌ | ✅ | 2 |
| 11 | conan-io__conan-17781 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 12 | conan-io__conan-17819 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 13 | conan-io__conan-17967 | ✅ | ✅ | ⬜ | ✅ | 2 |
| 14 | deepset-ai__haystack-8489 | ✅ | ✅ | ❌ | ✅ | 3 |
| 15 | deepset-ai__haystack-8525 | ✅ | ✅ | ❌ | ⬜ | 3 |
| 16 | deepset-ai__haystack-8619 | ✅ | ❌ | ❌ | ✅ | 2 |
| 17 | deepset-ai__haystack-8879 | ✅ | ❌ | ❌ | ⬜ | 2 |
| 18 | deepset-ai__haystack-8981 | ✅ | ✅ | ❌ | ✅ | 2 |
| 19 | deepset-ai__haystack-8993 | ✅ | ✅ | ❌ | ✅ | 2 |
| 20 | deepset-ai__haystack-9027 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 21 | dynaconf__dynaconf-1238 | ✅ | ✅ | ❌ | ✅ | 2 |
| 22 | encode__starlette-2812 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 23 | facebookresearch__hydra-3005 | ✅ | ✅ | ❌ | ✅ | 2 |
| 24 | falconry__falcon-2366 | ✅ | ✅ | ❌ | ✅ | 2 |
| 25 | instructlab__instructlab-2585 | ✅ | ✅ | ❌ | ⬜ | 3 |
| 26 | instructlab__instructlab-2886 | ✅ | ✅ | ❌ | ✅ | 2 |
| 27 | instructlab__instructlab-2927 | ✅ | ✅ | ❌ | ✅ | 2 |
| 28 | jazzband__tablib-613 | ✅ | ✅ | ❌ | ✅ | 2 |
| 29 | jupyterlab__jupyter-ai-1022 | ✅ | ✅ | ❌ | ✅ | 2 |
| 30 | jupyterlab__jupyter-ai-1125 | ✅ | ✅ | ⚠️ | ✅ | 1 |
| 31 | keras-team__keras-20396 | ✅ | ❌ | ❌ | ✅ | 2 |
| 32 | keras-team__keras-20534 | ✅ | ❌ | ❌ | ✅ | 2 |
| 33 | keras-team__keras-20880 | ✅ | ❌ | ❌ | ✅ | 2 |
| 34 | kozea__weasyprint-2387 | ✅ | ✅ | ❌ | ✅ | 2 |
| 35 | matplotlib__matplotlib-28933 | ✅ | ❌ | ❌ | ❌ | 2 |
| 36 | matplotlib__matplotlib-29007 | ✅ | ❌ | ❌ | ⬜ | 2 |
| 37 | matplotlib__matplotlib-29431 | ✅ | ❌ | ❌ | ❌ | 2 |
| 38 | matplotlib__matplotlib-29486 | ✅ | ❌ | ❌ | ❌ | 2 |
| 39 | matplotlib__matplotlib-29689 | ✅ | ❌ | ❌ | ❌ | 2 |
| 40 | modelcontextprotocol__python-sdk-222 | ✅ | ❌ | ❌ | ✅ | 2 |
| 41 | pdm-project__pdm-3237 | ✅ | ✅ | ❌ | ❌ | 2 |
| 42 | pdm-project__pdm-3250 | ✅ | ✅ | ❌ | ✅ | 2 |
| 43 | pdm-project__pdm-3314 | ✅ | ✅ | ❌ | ✅ | 2 |
| 44 | pdm-project__pdm-3374 | ✅ | ✅ | ❌ | ✅ | 2 |
| 45 | pdm-project__pdm-3419 | ✅ | ✅ | ⬜ | ❌ | 2 |
| 46 | projectmesa__mesa-2523 | ✅ | ✅ | ❌ | ✅ | 2 |
| 47 | pvlib__pvlib-python-2292 | ✅ | ✅ | ❌ | ✅ | 2 |
| 48 | pydata__xarray-10076 | ✅ | ✅ | ⬜ | ✅ | 2 |
| 49 | pydata__xarray-9760 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 50 | pydata__xarray-9765 | ✅ | ✅ | ❌ | ✅ | 2 |
| 51 | pylint-dev__pylint-10097 | ✅ | ✅ | ❌ | ✅ | 3 |
| 52 | pylint-dev__pylint-10240 | ✅ | ✅ | ❌ | ✅ | 2 |
| 53 | python-babel__babel-1164 | ✅ | ❌ | ❌ | ✅ | 2 |
| 54 | python-control__python-control-1064 | ✅ | ❌ | ❌ | ❌ | 2 |
| 55 | python-control__python-control-1142 | ✅ | ✅ | ❌ | ✅ | 2 |
| 56 | pytorch__torchtune-2066 | ✅ | ✅ | ❌ | ✅ | 2 |
| 57 | pytorch__torchtune-2139 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 58 | qtile__qtile-5154 | ✅ | ✅ | ❌ | ✅ | 2 |
| 59 | reflex-dev__reflex-4129 | ✅ | ✅ | ❌ | ❌ | 3 |
| 60 | reflex-dev__reflex-4347 | ✅ | ✅ | ❌ | ✅ | 2 |
| 61 | reflex-dev__reflex-4371 | ✅ | ✅ | ⚠️ | ✅ | 1 |
| 62 | reflex-dev__reflex-4427 | ✅ | ✅ | ❌ | ✅ | 2 |
| 63 | reflex-dev__reflex-4717 | ✅ | ✅ | ❌ | ✅ | 2 |
| 64 | reflex-dev__reflex-5039 | ✅ | ✅ | ⚠️ | ⬜ | 1 |
| 65 | run-llama__llama_deploy-372 | ✅ | ✅ | ⬜ | ✅ | 2 |
| 66 | run-llama__llama_deploy-397 | ✅ | ✅ | ❌ | ✅ | 2 |
| 67 | run-llama__llama_deploy-399 | ✅ | ✅ | ❌ | ✅ | 2 |
| 68 | run-llama__llama_deploy-438 | ✅ | ✅ | ❌ | ✅ | 2 |
| 69 | scrapy-plugins__scrapy-splash-324 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 70 | shapely__shapely-2255 | ✅ | ✅ | ⬜ | ✅ | 1 |
| 71 | sissbruecker__linkding-971 | ✅ | ✅ | ❌ | ✅ | 2 |
| 72 | sissbruecker__linkding-984 | ✅ | ✅ | ❌ | ✅ | 2 |
| 73 | sissbruecker__linkding-999 | ✅ | ✅ | ❌ | ✅ | 2 |
| 74 | sphinx-doc__sphinx-12975 | ✅ | ❌ | ❌ | ✅ | 2 |
| 75 | sphinx-doc__sphinx-13200 | ✅ | ✅ | ❌ | ✅ | 2 |
| 76 | sphinx-doc__sphinx-13261 | ✅ | ✅ | ❌ | ✅ | 2 |
| 77 | sphinx-doc__sphinx-13318 | ✅ | ✅ | ❌ | ✅ | 2 |
| 78 | stanfordnlp__dspy-1801 | ✅ | ✅ | ❌ | ⬜ | 2 |
| 79 | streamlink__streamlink-6338 | ✅ | ✅ | ❌ | ✅ | 2 |
| 80 | yt-dlp__yt-dlp-12684 | ✅ | ✅ | ❌ | ✅ | 2 |

### 5b. Resolved by ami-agent, not by tianxicode_deepseek-flash (56 tasks)

| # | instance_id | tianxicode_deepseek-flash | sapient-slingshot-agent_v3.4.0_gpt-5.6-sol | ami-agent | agav_gpt-5.5 | with trajectory |
|---|---|---|---|---|---|---|
| 1 | aws-cloudformation__cfn-lint-3764 | ❌ | ❌ | ✅ | ❌ | 2 |
| 2 | aws-cloudformation__cfn-lint-3767 | ❌ | ❌ | ✅ | ❌ | 3 |
| 3 | aws-cloudformation__cfn-lint-3768 | ❌ | ❌ | ✅ | ❌ | 2 |
| 4 | aws-cloudformation__cfn-lint-3770 | ❌ | ❌ | ✅ | ❌ | 2 |
| 5 | aws-cloudformation__cfn-lint-3779 | ❌ | ❌ | ✅ | ❌ | 2 |
| 6 | aws-cloudformation__cfn-lint-3789 | ❌ | ❌ | ✅ | ❌ | 2 |
| 7 | aws-cloudformation__cfn-lint-3805 | ❌ | ❌ | ✅ | ❌ | 2 |
| 8 | aws-cloudformation__cfn-lint-3817 | ❌ | ❌ | ✅ | ❌ | 2 |
| 9 | aws-cloudformation__cfn-lint-3821 | ❌ | ❌ | ✅ | ❌ | 2 |
| 10 | aws-cloudformation__cfn-lint-3854 | ❌ | ❌ | ✅ | ❌ | 2 |
| 11 | aws-cloudformation__cfn-lint-3856 | ❌ | ❌ | ✅ | ❌ | 2 |
| 12 | aws-cloudformation__cfn-lint-3862 | ❌ | ❌ | ✅ | ❌ | 2 |
| 13 | aws-cloudformation__cfn-lint-3875 | ❌ | ❌ | ✅ | ❌ | 2 |
| 14 | aws-cloudformation__cfn-lint-3890 | ❌ | ❌ | ✅ | ❌ | 2 |
| 15 | aws-cloudformation__cfn-lint-3947 | ❌ | ❌ | ✅ | ❌ | 2 |
| 16 | aws-cloudformation__cfn-lint-3982 | ❌ | ❌ | ✅ | ❌ | 2 |
| 17 | aws-cloudformation__cfn-lint-4002 | ❌ | ❌ | ✅ | ❌ | 2 |
| 18 | aws-cloudformation__cfn-lint-4009 | ❌ | ❌ | ✅ | ❌ | 2 |
| 19 | aws-cloudformation__cfn-lint-4016 | ❌ | ❌ | ✅ | ❌ | 2 |
| 20 | aws-cloudformation__cfn-lint-4023 | ❌ | ❌ | ✅ | ❌ | 2 |
| 21 | aws-cloudformation__cfn-lint-4032 | ❌ | ❌ | ✅ | ❌ | 2 |
| 22 | aws-cloudformation__cfn-lint-4051 | ❌ | ❌ | ✅ | ❌ | 2 |
| 23 | beeware__briefcase-2088 | ❌ | ✅ | ✅ | ✅ | 2 |
| 24 | beeware__briefcase-2214 | ❌ | ❌ | ✅ | ✅ | 2 |
| 25 | bridgecrewio__checkov-6893 | ❌ | ❌ | ✅ | ❌ | 2 |
| 26 | bridgecrewio__checkov-7002 | ❌ | ❌ | ✅ | ❌ | 2 |
| 27 | falconry__falcon-2419 | ❌ | ✅ | ✅ | ⬜ | 2 |
| 28 | fonttools__fonttools-3726 | ❌ | ✅ | ✅ | ❌ | 2 |
| 29 | geopandas__geopandas-3471 | ❌ | ❌ | ✅ | ❌ | 2 |
| 30 | huggingface__smolagents-285 | ❌ | ❌ | ✅ | ❌ | 2 |
| 31 | huggingface__smolagents-405 | ❌ | ❌ | ✅ | ❌ | 2 |
| 32 | huggingface__smolagents-843 | ❌ | ❌ | ✅ | ❌ | 2 |
| 33 | instructlab__instructlab-2526 | ❌ | ✅ | ✅ | ✅ | 2 |
| 34 | instructlab__instructlab-2540 | ❌ | ✅ | ✅ | ✅ | 2 |
| 35 | instructlab__instructlab-3060 | ❌ | ✅ | ✅ | ❌ | 2 |
| 36 | instructlab__instructlab-3118 | ❌ | ❌ | ✅ | ✅ | 2 |
| 37 | joke2k__faker-2162 | ❌ | ✅ | ✅ | ❌ | 2 |
| 38 | kedro-org__kedro-4387 | ❌ | ❌ | ✅ | ⬜ | 2 |
| 39 | kedro-org__kedro-4406 | ❌ | ❌ | ✅ | ❌ | 2 |
| 40 | kedro-org__kedro-4408 | ❌ | ❌ | ✅ | ❌ | 2 |
| 41 | kedro-org__kedro-4427 | ❌ | ❌ | ✅ | ⬜ | 2 |
| 42 | mikedh__trimesh-2354 | ❌ | ❌ | ✅ | ❌ | 2 |
| 43 | privacyidea__privacyidea-4226 | ❌ | ✅ | ✅ | ✅ | 2 |
| 44 | pybamm-team__pybamm-4816 | ❌ | ✅ | ✅ | ❌ | 2 |
| 45 | pypsa__pypsa-1091 | ❌ | ❌ | ✅ | ❌ | 2 |
| 46 | pypsa__pypsa-1112 | ❌ | ❌ | ✅ | ❌ | 2 |
| 47 | pypsa__pypsa-1172 | ❌ | ❌ | ✅ | ❌ | 2 |
| 48 | python-telegram-bot__python-telegram-bot-4626 | ❌ | ❌ | ✅ | ❌ | 2 |
| 49 | sissbruecker__linkding-995 | ❌ | ✅ | ✅ | ❌ | 2 |
| 50 | stanfordnlp__dspy-1609 | ❌ | ✅ | ✅ | ❌ | 2 |
| 51 | stanfordnlp__dspy-1741 | ❌ | ❌ | ✅ | ❌ | 2 |
| 52 | streamlink__streamlink-6328 | ❌ | ✅ | ✅ | ❌ | 2 |
| 53 | theoehrly__fast-f1-699 | ❌ | ✅ | ✅ | ✅ | 2 |
| 54 | tox-dev__tox-3409 | ❌ | ✅ | ✅ | ❌ | 2 |
| 55 | wemake-services__wemake-python-styleguide-3114 | ❌ | ✅ | ✅ | ✅ | 2 |
| 56 | wemake-services__wemake-python-styleguide-3195 | ❌ | ❌ | ✅ | ⬜ | 2 |
