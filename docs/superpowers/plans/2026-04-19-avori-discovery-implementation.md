# Avori Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## File Map

- `/Users/purplesprite/workflow/brands/avori-discovery/config.py`: config constants, env loading, output helpers
- `/Users/purplesprite/workflow/brands/avori-discovery/tikhub_client.py`: TikHub client creation and sample-data fallback
- `/Users/purplesprite/workflow/brands/avori-discovery/endpoints/__init__.py`: endpoint package marker
- `/Users/purplesprite/workflow/brands/avori-discovery/endpoints/search.py`: search and suggestion helpers
- `/Users/purplesprite/workflow/brands/avori-discovery/endpoints/trending.py`: hot-product helper
- `/Users/purplesprite/workflow/brands/avori-discovery/endpoints/detail.py`: enrich/detail and seller catalog helpers
- `/Users/purplesprite/workflow/brands/avori-discovery/scorer.py`: product scoring and ranking
- `/Users/purplesprite/workflow/brands/avori-discovery/output.py`: json + brief output
- `/Users/purplesprite/workflow/brands/avori-discovery/avori_discovery.py`: orchestration entrypoint
- `/Users/purplesprite/workflow/brands/avori-discovery/requirements.txt`: runtime dependencies
- `/Users/purplesprite/workflow/brands/avori-discovery/.env.example`: env documentation
- `/Users/purplesprite/workflow/brands/avori-discovery/tests/test_scorer.py`: scorer TDD
- `/Users/purplesprite/workflow/brands/avori-discovery/tests/test_output.py`: output TDD
- `/Users/purplesprite/workflow/brands/avori-discovery/tests/test_runner.py`: orchestration TDD

## Tasks

- [ ] Write failing tests for scoring, ranking, early-window logic, and output files.
- [ ] Run the tests and confirm the expected failures.
- [ ] Implement the minimal `scorer.py` and `output.py` code to satisfy the tests.
- [ ] Run the focused tests and confirm they pass.
- [ ] Write a failing runner test for clean execution and daily brief output.
- [ ] Run the runner test and confirm the expected failure.
- [ ] Implement `config.py`, `tikhub_client.py`, endpoint modules, and `avori_discovery.py` with sample-data fallback.
- [ ] Run the full test suite and confirm all tests pass.
- [ ] Create a local virtualenv, install requirements, and run `python avori_discovery.py` cleanly from the project environment.
- [ ] Verify the stdout brief plus the two expected output files exist for today.
