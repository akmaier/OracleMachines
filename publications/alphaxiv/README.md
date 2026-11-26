# OracleMachines on alphaXiv

The user authorized publication and daily updates on 26 November 2026, including
Andreas Maier and GPT Astra (OpenAI AI research assistant) in the byline. The AI
role must remain explicit, both in the manuscript and the submission disclosure.
`publication.json` records the live paper and the latest verified published state.

Use `scripts/alphaxiv_mcp.py` with the local ignored `alphaxiv.org` credential.
The client initializes the official sessionless MCP endpoint for every call.
`tools` retrieves current schemas; `call get_upload_instructions` retrieves the
current upload procedure. The public PDF upload endpoint rejects API-key headers,
so `upload PATH.pdf` sends only the authorized PDF; authenticated `publish_paper`
then attaches that upload to the user's account. A custom User-Agent is required
in this environment (the default urllib client received HTTP 403).

Before publishing a daily revision, select a committed verified research state,
update the publication date and evidence revision in the manuscript, build it,
inspect altered pages, and preserve the exact submitted PDF and metadata. Check
all new mathematical claims against their proofs and resource assumptions.
Maintain explicit limits on arbitrary SAT. An experiment that has not passed its
checks must not be folded into the publication just because a daily run fired.

Invoke `publish_paper` with `new_version_of` set to the existing paper URL from
`publication.json`; the first submission alone omits it. Preserve approved author
order, title and explicit AI disclosure. Capture the returned status and confirm
publication before advancing the published revision. If status is pending, retain
the upload and submission details and follow that submission; do not blindly
publish another one. Do not duplicate unchanged versions. Record failures and
retain earlier published PDFs and metadata. Update this registry and commit/push
the verified publication checkpoint.

Never print the token, include it in a command argument, or add its file to git.
The API client performs no automatic publication: upload and publish are explicit
commands. No account credentials or uploaded private notes belong in evidence.
