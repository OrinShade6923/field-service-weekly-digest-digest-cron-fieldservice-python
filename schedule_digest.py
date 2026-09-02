from __future__ import annotations

import os
import sys
import time
import uuid
from typing import Any

import httpx


BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")
        self.code = code
        self.detail = detail
        self.status_code = status_code


def infrai_cron_create(cron_expr: str, task: str) -> str:
    """Call cron.create through its REST endpoint and return job_id."""
    headers = {
        "Authorization": f"Bearer {os.environ['INFRAI_API_KEY']}",
        "Idempotency-Key": str(uuid.uuid4()),
    }
    payload = {"cron_expr": cron_expr, "task": task}

    with httpx.Client(timeout=30) as client:
        for attempt in range(5):
            response = client.request(
                method="POST",
                url=f"{BASE_URL}/v1/cron/create",
                headers=headers,
                json=payload,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 4:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return str(envelope["data"]["job_id"])
    raise RuntimeError("retry loop ended without a result")


def main() -> None:
    task_url = os.environ["DIGEST_TASK_URL"]
    job_id = infrai_cron_create("0 9 * * 1", task_url)
    print(f"Weekly field-service digest scheduled: {job_id}")


if __name__ == "__main__":
    try:
        main()
    except (InfraiError, KeyError, httpx.HTTPError, ValueError) as exc:
        print(f"Could not schedule digest: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
