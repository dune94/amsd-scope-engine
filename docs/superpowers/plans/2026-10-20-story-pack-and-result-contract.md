# Story pack and result contract (scope engine) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the scope engine build a story pack, run from one, and write a versioned result contract, so the estimations app can drive it.

**Architecture:** Two small new modules (`scope/contract.py`, `scope/pack.py`) plus a thin change to `flow.go` and the command line. Nothing about the agents or the formula changes.

**Tech Stack:** Python 3.12, pytest, the existing `scope` package (`jira.story`, `llm.call`, `flow.go`).

**Spec:** the estimations repo's `docs/superpowers/specs/2026-10-20-scope-fed-estimation-pipeline-design.md`, sections 4.3 and 4.12. This plan is the scope-engine half; the app plan depends on it.

## Global Constraints

- Jira and Confluence are read-only.
- Every subprocess runs under the memory-cap wrapper; scratch files are deleted by the run.
- All organisation-specific values live in untracked local configuration; committed files are neutral (run `scripts/check_clean.py` before each commit).
- No model or provider names in published diagrams or slides.
- Everything tunable is configuration, not code.
- Default behaviour (no new flags) must be exactly as today.

## Review Focus

- A pack whose `schema_version` is missing or unknown: refused with a clear error, never half-read.
- A pack that references an image path that no longer exists: the story still runs, the image is listed as "not read".
- `--story-pack` pointing at a folder the run must not delete: the run never removes it (including on failure).
- Reviewer notes that are empty, very long (over 4,000 characters) or contain markup: stored verbatim, length-capped by configuration, never executed.
- A ticket whose text is unchanged but whitespace differs: same `story_hash`.

---

### Task 1: Result contract fields

**Files:**
- Create: `scope/contract.py`, `tests/test_contract.py`
- Modify: `scope/flow.py` (call the two functions), `config/scope.yml` (add `contract:` block is not needed; version is a constant)

**Interfaces:**
- Produces: `SCHEMA_VERSION = 1`; `story_hash(title: str, text: str) -> str` (SHA-256 hex of the title and text with all runs of whitespace collapsed to one space, lower-cased line endings irrelevant); `stamp_story(res: dict, title: str, text: str) -> None` (sets `res['story_hash']`); `add_contract_fields(res: dict) -> None` (sets `res['schema_version'] = 1` and `res['pert']` = a copy of `res['planning']['pert']` when present, else `None`).

- [ ] **Step 1: Write the failing tests** in `tests/test_contract.py`: `test_story_hash_ignores_whitespace_differences` (two texts differing only in spaces/newlines give equal hashes; a changed word gives a different hash); `test_stamp_story_sets_hash`; `test_add_contract_fields_copies_pert` (`res = {'planning': {'pert': {'expected_sp': 5}}}` gives `res['pert'] == {'expected_sp': 5}` and `res['schema_version'] == 1`); `test_add_contract_fields_without_planning` (`res['pert'] is None`).
- [ ] **Step 2: Run** `~/.claude/bin/bounded --want 1024 -- python3 -m pytest tests/test_contract.py -q`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** the functions above in `scope/contract.py`.
- [ ] **Step 4: Wire into `flow.go`:** call `contract.stamp_story(res, title, text)` right after the story is loaded and `contract.add_contract_fields(res)` in the `finally` block before `result.json` is written.
- [ ] **Step 5: Run** the full suite (`python3 -m pytest -q`). Expected: all pass.
- [ ] **Step 6: Commit** `feat: result contract v1 (schema_version, story_hash, named pert block)`.

### Task 2: Story pack (build, load, notes)

**Files:**
- Create: `scope/pack.py`, `tests/test_pack.py`
- Modify: `config/scope.yml` (add `pack: {max_notes_chars: 4000}`)

**Interfaces:**
- Consumes: `jira.story(key: str, inputs_dir: pathlib.Path) -> (title, text, images, inputs)` (existing).
- Produces: `build_pack(key: str, dest: pathlib.Path) -> pathlib.Path` (writes `dest/pack.json` and copies images to `dest/images/`; returns the pack path); `load_pack(path: pathlib.Path) -> tuple[str, str, list[str], dict]` (title, text, absolute image paths that exist, inputs; raises `ValueError` for a missing or unknown `schema_version`; images that no longer exist are dropped and added to `inputs['attachments_not_read']` with reason `image file missing`); `append_notes(path: pathlib.Path, notes: str, date: str) -> None` (appends a section headed `REVIEWER NOTES (<date>)` to `text`, records the note in a `reviewer_notes` list, truncates to `max_notes_chars`).
- Pack format: JSON `{schema_version: 1, key, title, text, images: [relative paths], inputs, reviewer_notes: [], built_at}`.

- [ ] **Step 1: Write the failing tests** in `tests/test_pack.py` (monkeypatch `scope.jira.story` to return a fixture and write one image file into the dir it is given): `test_build_pack_writes_file_and_copies_images`; `test_load_pack_returns_story_tuple` (title/text equal the fixture, image path absolute and exists); `test_load_pack_rejects_unknown_version` (`ValueError`, message contains `schema_version`); `test_load_pack_drops_missing_image_and_lists_it`; `test_append_notes_adds_dated_section_and_changes_story_hash` (uses `contract.story_hash`); `test_append_notes_truncates_long_notes`; `test_notes_with_markup_are_stored_verbatim`.
- [ ] **Step 2: Run** `tests/test_pack.py`. Expected: FAIL.
- [ ] **Step 3: Implement** the three functions in `scope/pack.py`; use `jira.story` unchanged for the reading.
- [ ] **Step 4: Run** `tests/test_pack.py`, then the full suite. Expected: PASS.
- [ ] **Step 5: Commit** `feat: story pack (build, load, reviewer notes)`.

### Task 3: Run from a pack; command line; installed copy

**Files:**
- Create: `tests/test_resolve_story.py`, `docs/result-contract-v1.md`
- Modify: `scope/flow.py`, `scope/__main__.py`, `tests/test_clean.py` is untouched

**Interfaces:**
- Consumes: `pack.load_pack`, `pack.build_pack`, `jira.story`, `contract.*`.
- Produces: `flow.resolve_story(key: str, run_dir: pathlib.Path, pack_path: pathlib.Path | None) -> tuple[str, str, list[str], dict, pathlib.Path, bool]` (title, text, images, inputs, working directory for the agents, `owned` = whether the run created the directory and may delete it); `flow.go(key: str, drivers_only: bool = False, pack_path: pathlib.Path | None = None)`; command line `python3 -m scope KEY --build-pack DIR` and `python3 -m scope KEY --run --story-pack FILE`.

- [ ] **Step 1: Write the failing tests** in `tests/test_resolve_story.py`: `test_with_pack_never_calls_jira` (monkeypatch `jira.story` to raise `AssertionError`; `owned` is `False`; working directory is the pack's folder); `test_without_pack_fetches_and_owns` (`jira.story` called once; `owned` is `True`); `test_failed_run_does_not_delete_pack_folder` (pack folder still exists after `flow.go` raises).
- [ ] **Step 2: Run** the file. Expected: FAIL.
- [ ] **Step 3: Implement** `resolve_story` and make `flow.go` use it; in the `finally` block delete the inputs folder only when `owned`. Add the two command-line options to `__main__.py` (`--build-pack` writes the pack and exits without running any agent; `--story-pack` requires `--run`; any other combination exits with a usage message).
- [ ] **Step 4: Document** the contract in `docs/result-contract-v1.md` (every key the app reads: `schema_version`, `story_hash`, `required`, `alternatives`, `codelines`, `blast_required`, `planning`, `pert`, `drivers`, `inputs`, `flags`, `proof`; neutral wording).
- [ ] **Step 5: Run** the full suite and `python3 scripts/check_clean.py`. Expected: all pass, `clean`.
- [ ] **Step 6: Sync the installed copy** (copy changed files to the installed scope-engine folder, run its tests under the cap), then **Commit** `feat: run from a story pack, build-pack command, contract doc`.
