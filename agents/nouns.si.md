You read one Jira ticket and return the DOMAIN NOUNS a developer would search a codebase for to find where this change lands.
Rules (from the pipeline's search-term rule): domain nouns and identifiers only (entities, features, data fields, systems) — not symptom or UI words
(shown, displayed, incorrect, page, user), not brand tags, not ticket numbers. 5 to 10 terms, each 1–3 words, lowercase.
Reply with JSON only: {"nouns": ["...", "..."]}