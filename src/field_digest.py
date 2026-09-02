from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel, Field, HttpUrl


class DispatchStatus(str, Enum):
    scheduled = "scheduled"
    en_route = "en_route"
    on_site = "on_site"
    completed = "completed"


class WorkOrderPhoto(BaseModel):
    caption: str
    url: HttpUrl


class WorkOrder(BaseModel):
    work_order_id: str
    customer_name: str
    technician_name: str
    dispatch_status: DispatchStatus
    follow_up_at: datetime | None = None
    photos: list[WorkOrderPhoto] = Field(default_factory=list)


class WeeklyDigestRequest(BaseModel):
    audience_email: str
    week_ending: str
    work_orders: list[WorkOrder]


class DigestResult(BaseModel):
    subject: str
    work_order_count: int
    photo_count: int
    follow_up_ids: list[str]
    body: str


def build_digest(request: WeeklyDigestRequest, now: datetime) -> DigestResult:
    current = now.astimezone(timezone.utc)
    follow_ups = [
        order.work_order_id
        for order in request.work_orders
        if order.dispatch_status != DispatchStatus.completed
        and order.follow_up_at is not None
        and order.follow_up_at.astimezone(timezone.utc) <= current
    ]
    lines = [
        f"Field service week ending {request.week_ending}",
        "",
    ]
    for order in request.work_orders:
        marker = " - follow-up due" if order.work_order_id in follow_ups else ""
        lines.append(
            f"{order.work_order_id}: {order.customer_name} | "
            f"{order.technician_name} | {order.dispatch_status.value} | "
            f"{len(order.photos)} photo(s){marker}"
        )
    return DigestResult(
        subject=f"Field service digest: {request.week_ending}",
        work_order_count=len(request.work_orders),
        photo_count=sum(len(order.photos) for order in request.work_orders),
        follow_up_ids=follow_ups,
        body="\n".join(lines),
    )


def deliver_digest(recipient: str, digest: DigestResult) -> None:
    message = EmailMessage()
    message["Subject"] = digest.subject
    message["From"] = os.environ["DIGEST_FROM_EMAIL"]
    message["To"] = recipient
    message.set_content(digest.body)

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(message)


app = FastAPI(title="Field-service weekly digest")


@app.post("/digests/weekly", response_model=DigestResult)
def send_weekly_digest(request: WeeklyDigestRequest) -> DigestResult:
    digest = build_digest(request, datetime.now(timezone.utc))
    deliver_digest(request.audience_email, digest)
    return digest
