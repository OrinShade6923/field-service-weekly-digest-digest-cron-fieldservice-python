import httpx

import schedule_digest


def test_schedule_uses_exact_cron_body_and_reads_job_id(monkeypatch) -> None:
    seen: dict[str, object] = {}
    real_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["body"] = request.read().decode()
        seen["idempotency"] = request.headers["Idempotency-Key"]
        return httpx.Response(200, json={"ok": True, "data": {"job_id": "job_weekly_42"}, "error": None, "metadata": {}})

    transport = httpx.MockTransport(handler)
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: real_client(transport=transport, **kwargs))

    result = schedule_digest.infrai_cron_create("0 9 * * 1", "https://example.com/digests/weekly")

    assert result == "job_weekly_42"
    assert seen["method"] == "POST"
    assert seen["body"] == '{"cron_expr":"0 9 * * 1","task":"https://example.com/digests/weekly"}'
    assert seen["idempotency"]
