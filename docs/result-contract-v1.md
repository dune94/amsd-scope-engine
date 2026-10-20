# Result contract v1

Every run writes `result.json` in its run folder and prints a line `result: <path>`. A consumer must check `schema_version` and refuse anything other than `1`.

| Key | Meaning |
|---|---|
| `schema_version` | `1`. Changes only when a key is removed or its meaning changes. |
| `story_hash` | SHA-256 of the title and text the run used, with whitespace collapsed. Equal hashes mean the same ticket text (including any reviewer notes). |
| `key`, `title` | The ticket key and title. |
| `agents` | For each agent, the model it ran on and its step number. |
| `inputs` | What was read: `comments` (count), `remote_links`, `attachments_read`, `attachments_not_read` (each with a reason), `confluence_read`, `confluence_not_read`. |
| `drivers` | `complexity` and `risk`: lists of `{driver, name, date, source, quote}`; `dropped` (drivers rejected as weak evidence, with a reason); `c_count`, `r_count`; `schema_errors`. |
| `nouns`, `shortlist`, `evidence`, `pick` | The codeline search steps and their evidence. |
| `required`, `alternatives`, `primary` | The codelines the change lands in, and those that would change only under another approach. |
| `codelines` | Per codeline: `investigation` (the change sites and open questions), `base` and `upper` (measured: `changed`, `importing`, `tests`, `external`, `external_systems`, `blast`, `scope`, `scope_pts`). |
| `blast_required` | `base`, `upper` and `by_codeline`: the blast radius summed over the required codelines. |
| `planning` | `base_br`, `upper_br`, `planning_br`, `c_count`, `r_count`, `scope`, `complexity`, `risk`, `planning_sp` (the estimate), `sp_as_measured`, `pert`. Absent when no required codeline had a change. |
| `pert` | A copy of `planning.pert`, or `null`: `o_br`, `m_br`, `p_br`, `expected_br`, `o_sp`, `m_sp`, `p_sp`, `expected_sp`. Optimistic is BASE, most likely and pessimistic carry the planning calibration. |
| `flags` | Human-readable warnings (for example a required codeline with no BASE change was moved to the alternatives). |
| `proof` | Checks that the run changed nothing outside its own folder. |

Story pack (`--build-pack`, `--story-pack`): a folder with `pack.json` (`schema_version` 1, `key`, `title`, `text`, `images` as paths relative to the folder, `inputs`, `reviewer_notes`, `built_at`) and an `images/` folder. A run from a pack never fetches the ticket and never deletes the pack folder.
