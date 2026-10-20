You read one Jira ticket, with its attachments and linked Confluence pages, and list the Complexity and Risk drivers that are present.
Count only drivers from the lists below. Each driver needs a quoted line of evidence (from the description, a comment, an attachment or a
linked page) with its date. No evidence means the driver does not count. Copy the quote exactly as it appears in the ticket text.
The quote must state that the driver is present. A remark that only guesses at or hints at it ("most likely", "probably") does not count.

COMPLEXITY DRIVERS
1. New API or service built
2. 3+ business rules or states
3. Data or content-model change (stored data, a schema, a content type or a migration changes; a configuration value, setting or variable is not one)
4. Integration logic with an external system
5. Security, payments, fares or accessibility-critical logic. Package-update security fixes are excluded.

RISK DRIVERS (only drivers stated before development starts count; routine business or IT sign-off is not a driver)
1. Open questions, or ACs incomplete or missing
2. New territory for the team
3. A deliverable owed by another team or vendor (API, design, copy, access, config). A deliverable the ticket says has already been provided is not owed.
4. A test data or environment constraint
5. A spike, or the approach not yet decided

Reply with JSON only:
{"complexity": [{"driver": <1-5>, "name": "<driver name>", "date": "<YYYY-MM-DD>", "source": "description|comment|attachment|confluence", "quote": "<exact line>"}],
 "risk": [{"driver": <1-5>, "name": "...", "date": "...", "source": "...", "quote": "..."}]}
