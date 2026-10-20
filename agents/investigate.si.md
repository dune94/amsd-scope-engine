TOOLS (Bash only, at most {max_tool_calls} calls in total; run them from the working directory):
  codegraph explore "<domain nouns>"   relevant symbols' source + call paths   START HERE
  codegraph query "<symbol>" --json    definition sites
  codegraph callers "<symbol>"         who calls it        codegraph callees "<symbol>"   what it calls
  codegraph impact "<symbol>"          what changing it affects
  codegraph node "<file or symbol>"    source with line numbers + dependents
  rg -n "<text>"                       plain text search
Method: search domain nouns, read the top hits, trace callers/callees until you know which files must change to deliver EVERY acceptance
criterion. Include configuration, content-model / CMS schema and migration files when the ticket needs them. Do not edit anything.

Classify each site: role = "produces" (makes the new value exist: fetches, queries, computes, defines the content type),
"carries" (moves / renders / stores a value produced elsewhere), or "verifies" (no change, confirm only).
BASE = the minimum set that delivers the ACs. UPPER = BASE plus optional or uncertain sites.

HOW EACH EXISTING FILE IS LISTED (this decides how dependent code is counted, so be exact):
  "logic"        the file's EXISTING behaviour changes: an existing function, component, query, mapping or condition is edited.
                 Every file that imports it is affected.
  "exports_only" the file only GAINS new things and nothing existing changes: a new constant, enum member, type/interface field,
                 new exported function, new event name, new i18n key. Only files that will use the new names are affected.
  "new"          files that do not exist yet.
  A shared file (analytics service, constants, types, schema) that only gets an addition is "exports_only", not "logic".
New files that do not exist yet go in "new" with the path they would most likely have.

Reply with JSON only:
{"base": {"logic": ["<repo-relative path>", ...], "exports_only": [...], "new": [...]},
 "upper": {"logic": [...], "exports_only": [...], "new": [...]},
 "external_systems_base": ["<system the BASE change itself integrates with, e.g. a headless CMS>", ...],
 "external_systems_upper": ["<systems the UPPER change integrates with>", ...],
 "sites": [{"file": "...", "function": "...", "role": "produces|carries|verifies", "change": "...", "in": "base|upper"}],
 "open_questions": ["..."]}