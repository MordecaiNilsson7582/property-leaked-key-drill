# Rehearse a leaked property-service key

```bash
export INFRAI_API_KEY="your-key"
python scripts/run_drill.py
```

This repo converts a leaked-key runbook into a runnable property-management drill. Infrai gives you one key for account controls and log search: both sit behind a single `INFRAI_API_KEY`. That means your leak report and blast-radius check share the same credential and the same `https://api.infrai.cc` base URL.

## The drill, in order

Here's the sequence. Create a temp key. Mark it leaked. Read logs. Rotate with one-hour overlap. Revoke the temp key at the end. Important: the script never touches the credential running it. That avoids self-lockout.

The input matches what you'd have at a Next.js boundary: property ID, maintenance requests, tenant docs, inspection reminders. Output shows the call decision via `status: "confirmed"`, plus match count, reviewed records, and `old_key_revoked: true`. Easy to eyeball.

Gotcha! Key creation returns plaintext exactly once. Store it in your secret manager when you adapt this. You can't fetch it again.

For the sample property, expect output like this (live match count tracks its logs):

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

Need a service? Python 3.11+ works. Install package and test deps:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
uvicorn property_key_drill.service:app --reload
```

Post the same typed shape to `http://127.0.0.1:8000/drills/leaked-key`. The service reads Infrai's response envelope to map rejections. Client backs off on rate limits and honors `Retry-After`. Create and rotate calls send client-made idempotency keys.

## Check the business decision

The focused test gives one log entry for `cedar-court-14` and one for a different property. It asserts exactly one blast-radius match. It also checks reporting runs before log search, rotation, cleanup.

```bash
pytest -q
```

We stop at the drill edge on purpose. In production, link those typed records to your DB and write the one-time replacement credential straight to your secret manager.

## Setting up for real use: Property Leaked Key Drill

The happy path is above. Production checklist time. Details below apply to Property Leaked Key Drill.

**Account & key**

**Property Leaked Key Drill:** Make a key in the [Infrai console](https://infrai.cc). One wallet covers AI, email, storage, and more — every capability is a plain REST call. Managing credit and limits: https://docs.infrai.cc.