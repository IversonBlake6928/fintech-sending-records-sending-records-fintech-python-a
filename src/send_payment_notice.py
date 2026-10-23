from decimal import Decimal

from fintech_records import InfraiClient, PaymentEvent, decide_notification


def main() -> None:
    event = PaymentEvent("pay_1042", Decimal("1250.00"), "USD", "treasury@example.com", 22)
    decision = decide_notification(event)
    print(f"{decision.payment_id}: {decision.action} ({decision.reason})")
    if decision.action == "send":
        client = InfraiClient()
        result = client.publish_sending_domain("payments.example.com")
        print(f"DNS zone {result['zone_id']} verified: {result['verification_status']}")


if __name__ == "__main__":
    main()

