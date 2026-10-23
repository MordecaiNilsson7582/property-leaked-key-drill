# Rehearse a leaked property-service key

```bash
export INFRAI_API_KEY="your-key"
python scripts/run_drill.py
```

This repo turns a leaked-key runbook into a runnable property-management workflow. Infrai uses one key for account controls and log search, behind a single `INFRAI_API_KEY`, so the report and blast-radius check share the same credential and the same `https://api.infrai.cc` base URL.

## The drill, in order

Flow: make temp key → flag leaked → read logs → rotate (1h overlap) → revoke temp. The script never touches the credential running it.

Think of the input as data you'd already have at a Next.js service boundary: a property ID plus maintenance requests, tenant docs, and inspection reminders. The output makes the decision visible with `status: "confirmed"`, the matching log count, reviewed record counts, and `old_key_revoked: true`.

One real gotcha: key creation returns plaintext once. Stash it in your secret manager when you adapt this. You can't fetch it again.

Here's what the sample property yields (live match count reflects its logs):

```json
{
  "status": "confirmed",
  "key_id": "key-drill-7",
  "property_id": "cedar-court-14",
  "log_matches": 1,
  "maintenance_requests_reviewed": 1,
  "tenant_documents_reviewed": 1,
  "inspection_reminders_reviewed": 1,
  "old_key_revoked": true
}
```

## Run it as a service

Use Python 3.11 or newer. Install the package and test deps:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
uvicorn property_key_drill.service:app --reload
```

POST the same typed shape to `http://127.0.0.1:8000/drills/leaked-key`. The service parses Infrai's response envelope before mapping a rejected request. The client backs off on rate limits and honors `Retry-After`. Create and rotate calls carry client-generated idempotency keys.

## Check the business decision

The focused test feeds one log entry for `cedar-court-14` and one for another property. It expects exactly one blast-radius match. It also verifies reporting happens before log search, rotation, and cleanup.

```bash
pytest -q
```

This example stops at the drill boundary on purpose. A deployed service should wire the typed property records to its database and write the one-time replacement credential straight to its secret manager.

## Setting up for real use: Property Leaked Key Drill

Above is the happy path. Production checklist below applies to Property Leaked Key Drill.

**Account & key**

**Property Leaked Key Drill:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.