# Messenger App Review preparation

App: TCSO Membership Assistant (1649260566638800)
Page: Third-Country Supporters Organization (1225161934021706)
Privacy and deletion instructions: https://tcso.world/privacy/

## Purpose and requested permission

TCSO uses pages_messaging to receive questions initiated by visitors to its own Page and respond with membership registration guidance. The app offers an automated greeting, optional DeepSeek FAQ responses after the visitor types AI, and human handoff when the visitor types HUMAN, STOP, ADMIN or sends an application reference. It does not send unsolicited marketing messages, process payments or approve membership. Only the TCSO Page has a webhook subscription.

## Reviewer walkthrough

1. Open https://m.me/TCSODL with a reviewer account permitted by Meta to test the app.
2. Send Hello. Observe the automated greeting and disclosure of the AI provider.
3. Send AI. Observe confirmation of optional AI processing and HUMAN command.
4. Ask: Is the US$30 fee monthly? Observe the one-time fee explanation.
5. Ask for help registering. Observe the tcso.world/membership/ link and registration card and email verification / application / Messenger reference steps.
6. Send HUMAN. Observe the human-handoff acknowledgement.
7. Send another question. Observe that automated replies stay paused.
8. Send AI to opt in again if needed.

Application references must not be invented or represented as approved. The assistant acknowledges receipt of reference text and asks staff to review it; it does not look up applicant records.

## Data handling

Webhook payloads are validated with the Meta app-secret HMAC. Message IDs are deduplicated in private SQLite. Message text clears after processing; queue metadata expires after two days. Page-scoped identifiers and AI/human preference expire after 30 days. DeepSeek receives only the current opt-in question, with basic email/long-number redaction, not Page tokens or application database contents. No conversation-history memory is forwarded. Secrets are root-only environment files outside the repository. Staff monitor the Page inbox. Provider retention is governed by provider policies.

## Current status

Published November 8, 2026. The owner confirmed a successful non-role Facebook account reply test. Server checks recorded 11 processed events from three distinct senders with no failed events. Meta currently labels pages_messaging Ready for testing. Adding it to App Review presents an irreversible Tech Provider registration requirement, then business verification and review. Do not claim advanced access or completed review until Meta confirms it. Legal business ownership and data-handling attestations must come from the account owner. No screencast or review submission has been submitted yet.
