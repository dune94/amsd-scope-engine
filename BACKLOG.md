# Backlog: scope engine

Each item starts with a spec or a decision, then tests (no invented requirements). IDs are stable; do not reuse them.

| ID | Added | Item | What to do | Owner / needs |
|---|---|---|---|---|
| SC-BL-001 | 2026-10-20 | **Comment date cutoff.** All ticket comments count as driver evidence, including ones written after development started, but the Risk rule counts only what was stated before development starts. | Add an "as of" switch that drops comments, attachments and page versions newer than a date. | Decision: a date passed in per run, or each ticket's own development start date |
| SC-BL-002 | 2026-10-20 | **UPPER blast radius is unstable.** Repeat runs of one story gave 19 to 143 on both Opus and Sonnet; it only moves the PERT high point, not the planning SP. | Tighten the UPPER definition (named, evidenced extra sites only), or present it as indicative only. Measure on repeated runs. | Decision |
| SC-BL-003 | 2026-10-20 | **Shelved: per-driver checklist agent** (`agents/drivers_checklist.*`, untracked). In repeated runs it was no more stable than the current agent and cost about 30% more. | Keep local, or delete. Revisit only if driver flipping returns. | Decision: leave or remove |
| SC-BL-004 | 2026-10-20 | **Installer polish.** A "still blank in .env" warning prints before the real values are copied in; the installer does not copy `config.local/`, so 4 tests skip on a fresh install. | Hide the warning when `--env-from` is given; add an option to copy `config.local/` from a source folder. | Small; spec first |
| SC-BL-005 | 2026-10-20 | **Evidence-length rule side effect.** The 4-word minimum rejects any shorter quote (about 1 in 60 earlier quotes would have been rejected). | Review rejected quotes after a few PIs; adjust `drivers.min_quote_words` if real evidence is being lost. | Review |
