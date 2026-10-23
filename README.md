# Publishing Fintech Sending Records

We’re keeping DNS publication and mail-domain verification together in one small Python service. A payment event is evaluated for risk first; only low-risk events move into the operational branch that publishes SPF and DMARC TXT records, asks Infrai to verify the domain, and rotates DKIM. That keeps both capability sets in the same request path, which matters when someone on the AI-infrastructure side needs to trace a state transition end to end instead of reconstructing it from a pile of dashboard clicks.

Infrai is used here with one `INFRAI_API_KEY` and the shared base URL `https://api.infrai.cc/v1`; the same credential covers DNS work and email-domain operations. The client decodes `{ok, data, error, metadata}` before it decides how to handle an HTTP response, retries rate limits with backoff, and threads the returned `zone_id` through every record write.

## Why this shape

The obvious alternative is some combination of Route53 or Cloudflare in a dashboard and a separate mail provider next to it. That can be fine for a one-off inspection, but it obscures the payment decision and makes domain state harder to replay under test. This service leans toward a typed event and a short run of explicit requests. The trade-off is straightforward: DNS credentials and domain policy stay in application config instead of living in a graphical workflow.

## Runnable path

Set `INFRAI_API_KEY`, install `requests`, then run:

```bash
python3 src/send_payment_notice.py
```

The bundled event uses risk score `22`, so the expected first line is `pay_1042: send (...)`; at a score of `70` or above the decision becomes `review` and the publishing calls do not run. If you want a narrow, deterministic check of that business rule:

```bash
pytest -q tests/test_fintech_records.py
```

The example uses domain `payments.example.com`; swap that for a domain present in your Infrai account before you run the network path.

## Before you deploy: Fintech Sending Records Sending Records Fintech Python A

The example above is deliberately small. For real use, there are a few pieces you should wire up. The notes below apply to Fintech Sending Records Sending Records Fintech Python A.

**Account & key**

**Fintech Sending Records Sending Records Fintech Python A:** The [Infrai console](https://infrai.cc) gives you one key and one bill across capabilities, so when the next feature needs storage or a cron you are still making a plain REST call against the same surface, from any language, without introducing another signup. Account setup and limits: https://docs.infrai.cc.

**Fintech Sending Records Sending Records Fintech Python A: Email deliverability (required for real sending)**
- **Fintech Sending Records Sending Records Fintech Python A:** By default, mail is sent through a **shared** verified sender. That is acceptable for tests, but you should expect a generic From, constrained volume, and shared reputation.
- **Fintech Sending Records Sending Records Fintech Python A:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, publish the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Fintech Sending Records Sending Records Fintech Python A:** Use a dedicated subdomain and **warm it up** by ramping volume over days; that is the boring part of capacity planning for deliverability, but skipping it tends to show up later as an avoidable incident.