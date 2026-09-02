from datetime import datetime, timezone

from src.field_digest import WeeklyDigestRequest, build_digest


def test_digest_flags_due_incomplete_follow_up_and_counts_photos() -> None:
    request = WeeklyDigestRequest.model_validate(
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
                        {"caption": "Compressor label", "url": "https://example.com/label.jpg"},
                        {"caption": "Installed relay", "url": "https://example.com/relay.jpg"},
                    ],
                },
                {
                    "work_order_id": "WO-1043",
                    "customer_name": "Union Clinic",
                    "technician_name": "Dev",
                    "dispatch_status": "completed",
                    "follow_up_at": "2026-08-12T10:00:00Z",
                    "photos": [],
                },
            ],
        }
    )

    digest = build_digest(request, datetime(2026, 8, 14, 9, tzinfo=timezone.utc))

    assert digest.follow_up_ids == ["WO-1042"]
    assert digest.photo_count == 2
    assert "WO-1042: North Street Bakery | Mina | on_site | 2 photo(s) - follow-up due" in digest.body
    assert "WO-1043" in digest.body
