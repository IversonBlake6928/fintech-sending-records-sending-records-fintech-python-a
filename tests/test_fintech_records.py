from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from fintech_records import PaymentEvent, decide_notification


def test_high_risk_payment_is_held_for_review():
    event = PaymentEvent("pay_9", Decimal("80.00"), "USD", "ops@example.com", 70)
    decision = decide_notification(event)
    assert decision.action == "review"
    assert decision.payment_id == "pay_9"
