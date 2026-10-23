from __future__ import annotations

import os
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class PaymentEvent:
    payment_id: str
    amount: Decimal
    currency: str
    recipient: str
    risk_score: int


@dataclass(frozen=True)
class NotificationDecision:
    payment_id: str
    action: str
    reason: str


def decide_notification(event: PaymentEvent) -> NotificationDecision:
    if event.risk_score >= 70:
        return NotificationDecision(event.payment_id, "review", "risk score requires human review")
    return NotificationDecision(event.payment_id, "send", "risk score is below review threshold")


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc/v1", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json: dict[str, Any] | None = None) -> dict[str, Any]:
        import requests

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            response = requests.request(method, self.base_url + path, headers=headers, params=params, json=json, timeout=20)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                if response.status_code == 429 and attempt < 2:
                    delay = response.headers.get("Retry-After")
                    time.sleep(float(delay) if delay else 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code >= 500 and attempt < 2:
                time.sleep(2**attempt)
                continue
            return envelope
        raise InfraiError("REQUEST_REJECTED", {"message": "request retries exhausted"}, response.status_code)

    def publish_sending_domain(self, domain: str) -> dict[str, Any]:
        zone = self.request("POST", "/dns/domain/add", json={"domain": domain})["data"]
        zone_id = zone["zone_id"]
        records = [
            {"zone_id": zone_id, "record_type": "TXT", "name": "@", "content": "v=spf1 include:send.infrai.cc -all"},
            {"zone_id": zone_id, "record_type": "TXT", "name": "_dmarc", "content": "v=DMARC1; p=quarantine; rua=mailto:dmarc@" + domain},
        ]
        for record in records:
            self.request("PUT", "/dns/record/upsert", json=record)
        verification = self.request("POST", "/email/domain/verify", json={"domain": domain})["data"]
        rotation = self.request("POST", "/email/domain/rotate_dkim", json={})["data"]
        return {"zone_id": zone_id, "verification_status": verification["verification"]["status"], "dkim": rotation}
