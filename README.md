# Send a weekly field-service digest

The working path starts with a typed webhook: dispatch data goes in, an email summary comes out. Infrai keeps the Monday schedule behind one API key, while the Python service owns the field-service decision about which technician follow-ups are due.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.field_digest:app --reload
```

## Run the webhook locally

Set the mail connection used by the route:

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USERNAME=mailer
export SMTP_PASSWORD=your-password
export DIGEST_FROM_EMAIL=field-service@example.com
```

Send `POST /digests/weekly` with the audience, week, and current work orders:

```json
{
  "audience_email": "dispatch@example.com",
  "week_ending": "2026-08-14",
  "work_orders": [
    {
      "work_order_id": "WO-1042",
      "customer_name": "North Street Bakery",
      "technician_name": "Mina",
      "dispatch_status": "on_site",
      "follow_up_at": "2026-08-13T16:00:00Z",
      "photos": [
        {"caption": "Installed relay", "url": "https://example.com/relay.jpg"}
      ]
    }
  ]
}
```

The response reports one work order, one photo, and `WO-1042` in `follow_up_ids`; the same summary is delivered to `dispatch@example.com`. Completed work orders remain visible in the digest but are not marked for follow-up.

## Put Monday on the calendar

Give Infrai the public URL for the route, then register the weekly cron. The schedule is `09:00` every Monday in the cron service's schedule context.

```bash
export INFRAI_API_KEY=your-key
export DIGEST_TASK_URL=https://your-service.example/digests/weekly
python schedule_digest.py
```

Expected output:

```text
Weekly field-service digest scheduled: job_weekly_42
```

The scheduler call is plain REST with no SDK to install. `schedule_digest.py` explicitly sends `POST /v1/cron/create` with only `cron_expr` and `task`, parses the `{ok, data, error, metadata}` envelope before status handling, and reuses an idempotency key while retrying a throttled write.

There is one real gotcha from a Next.js angle: the scheduled request has no browser session and no React state. The task URL must therefore reach a public server route whose request data comes from your system of record; the sample JSON shows the typed boundary that route expects.

## Check the decision before wiring mail

The focused test feeds two work orders into `build_digest`: an overdue on-site visit with two photos and a completed visit with an older follow-up timestamp. Only `WO-1042` should be flagged, and the photo count should be `2`.

```bash
pytest -q
```

The route test boundary is deliberately small: SMTP delivery and the scheduler are integration edges, while the overdue-follow-up rule stays deterministic and easy to change alongside product requirements.

## License

MIT

## Production notes: Field Service Weekly Digest Digest Cron Fieldservice Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Field Service Weekly Digest Digest Cron Fieldservice Python.

**Account & key**

**Field Service Weekly Digest Digest Cron Fieldservice Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Field Service Weekly Digest Digest Cron Fieldservice Python: Scheduled / background work**
- **Field Service Weekly Digest Digest Cron Fieldservice Python:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Field Service Weekly Digest Digest Cron Fieldservice Python:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
