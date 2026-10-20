# Scope engine — specification

Complexity-based estimation engine. Takes Jira stories, returns blast radius, Scope / Complexity / Risk, planning SP and a PERT range,
plus a per-codeline change manifest. The estimations app calls it when its engine switch is set to `complexity`; it reads Jira,
stores, reviews and presents. This project calculates only.

Decisions recorded 2026-10-20 (interview). Anything not written here is out of scope and is reported as a deviation, not built.

## S1 Runs locally first
S1.1 Runs on the local machine with local clones of the codelines and CodeGraph. A CodeMie Web / workflow port comes later and is not built now.
S1.2 Every process runs under `~/.claude/bin/bounded` (driver and every child). Memory caps are set in config.
S1.3 Disk-bounded: snapshots and downloads are deleted by the run; a finished run keeps only small result files.
S1.4 Jira and Confluence are read-only (GET only). Credentials come from the existing environment variables (`ATLASSIAN_*` / `JIRA_*`); none are stored in the project.
S1.5 Nothing under the folders listed in `paths.proof_unchanged` is read or written; every run checks it.

## S2 Nothing hard-coded
S2.1 Every agent is defined in `agents/<name>.yml`: system-instructions file, prompt template file, output JSON schema, tools, model, timeout, memory cap.
S2.2 System instructions (role, rules) and the prompt (the task: ticket, evidence) are separate files. Templates use named placeholders.
S2.3 The model is pinned per agent in config. Pinned values: nouns `claude-haiku-5-5`, drivers `claude-sonnet-5-5`, pick and investigate `claude-opus-5-5` (the model the earlier runs used). Cheaper models were chosen from a comparison against Opus on a set of delivered and planned stories (nouns: the earlier required codelines all stayed in the shortlist; drivers: Sonnet matched Opus, Haiku did not); pick and investigate have not been tested on a cheaper model.
S2.4 The LLM command (CLI name and flags) is set in config, so the CLI can be changed (e.g. to codemie-claude) without touching code.
S2.5 Paths, codeline excludes, brand-tag map, shortlist size, tool-call limits and timeouts are set in `config/scope.yml`.
S2.6 The formula (blast-radius weights, Scope cut-offs and points, Complexity and Risk thresholds and points, SP bands, planning calibration, PERT) is set in `config/formula.yml`.

## S3 Story input
S3.1 Story text comes from live Jira: title, description, acceptance criteria, comments.
S3.2 Jira attachments are read: images / screenshots (passed to the agents as images), text documents (PDF, DOCX, MD, TXT) and PowerPoint (PPT/PPTX), text extracted locally.
S3.3 Confluence pages linked from the story (description, comments, remote links) are read. Links on those pages are not followed.
S3.4 Per-story cap on attachments (defaults in config: at most 20 files, 25 MB in total, 30 pages / slides per document). Anything over the cap is listed in the manifest as "not read".
S3.5 Spreadsheets are not read.

## S4 Agents
S4.1 Domain nouns (1a): ticket → 5–10 domain nouns. No tools.
S4.2 Codeline pick (1d): ticket + shortlist evidence → required and alternative codelines. No tools.
S4.3 Code-around investigator (2a): one session per chosen codeline in its snapshot → BASE / UPPER change sets (logic / exports_only / new), external systems, change sites, open questions. Tools: codegraph explore / query / callers / callees / impact / node and rg only.
S4.4 Complexity / Risk drivers (new): ticket + attachments + linked pages → the drivers present, each with a dated quote. Driver lists and the evidence rule are the v3.9 lists below. No evidence → the driver does not count.
  Complexity: 1 new API or service built; 2 3+ business rules or states; 3 data or content-model change; 4 integration logic with an external system; 5 security, payments, fares or accessibility-critical logic (package-update security fixes excluded).
  Risk (stated before development starts; routine business or IT sign-off is not a driver): 1 open questions, or ACs incomplete or missing; 2 new territory for the team; 3 a deliverable owed by another team or vendor; 4 a test data or environment constraint; 5 a spike, or the approach not yet decided.
S4.5 The prompt text of 1a, 1d and 2a is carried over from the existing flow unchanged (only split into system instructions / prompt / schema).

## S5 Deterministic steps (unchanged behaviour)
S5.1 1b shortlist (rg over the configured codelines, named codelines, brand tags, noun co-occurrence), 1c snapshot + CodeGraph index, codeline demote / promote rules, 2b blast-radius measure: as the existing flow.
S5.2 Planning SP: Scope(BR × 1.4) + Complexity(drivers + 1) + Risk(drivers + 1) → band. BR is summed over required codelines.
S5.3 PERT: O = BASE BR, M = BASE × 1.4, P = UPPER × 1.4; (O + 4M + P) / 6 → SP.

## S6 Checks before use
S6.1 Tests (red/green): config and agent definitions load; rendered prompts for 1a / 1d / 2a are identical to the existing flow's; formula reproduces the v3.9 bands; caps applied to every child command.
S6.2 The drivers agent is run on the stories that already have Complexity / Risk ratings, one story at a time, memory-capped; differences from the existing ratings are reported story by story.
S6.3 One PI-12 story is run end to end on the new project. The exact command is shown before it runs.
S6.4 No historical / delivered-story verification is built or run.

## S7 Publishing
S7.1 Only code, config and prompts are committed. Nothing organisation-specific is committed: paths and credentials come from `.env`, organisation values from `config.local/` (codeline names, tags, org pattern, local prompt wording, original-prompt fixtures). Both are untracked and each change is backed up to a local folder outside the repository.
S7.2 `scripts/check_clean.py` scans every file git would commit against `config.local/forbidden.txt` and must report clean before each commit.
S7.3 Installer: Python dependencies in a virtual environment, a check that the required CLI tools are present (reported, not installed), `.env` created from `.env.example`, and the memory-cap script installed. The codelines are assumed to be on disk; their root is detected at install and written to `.env`.
