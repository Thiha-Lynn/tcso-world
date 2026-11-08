# TCSO intake on the existing Myo Taw AWS instance

Public frontend: https://tcso.world/membership/ (GitHub Pages).
Intake: POST https://myotaw.com/tcso-api/applications, proxied by nginx to 127.0.0.1:8766.
No Meta Page credentials are configured. The Messenger handoff copies an applicant-reviewed message, including the saved reference. The applicant must paste and send. AWS submissions do not automatically appear in Facebook's Page inbox.

## Operations

SSH alias: `myotaw-prod`. App code: `/opt/tcso-intake/`. Unit: `tcso-intake.service`.
Service runs as a dedicated unprivileged user; SQLite files are mode 0600 under `/var/lib/tcso-intake/` (0700), outside the web root. There is no public read/list endpoint. CORS allows TCSO domains and the GitHub Pages origin; consent, length/type/email validation, honeypot, request-size cap and 10 submissions/hour per daily hashed IP limit apply. Request IDs deduplicate retries; changed payloads require a new request ID.

Daily `tcso-intake-maintenance.timer` purges records older than 89 days (so daily cleanup is within the stated 90-day retention), prunes rate-limit hashes and refreshes a consistent private SQLite backup. This backup is on the same disk and does not provide disaster recovery. No personal information is included in the public repository. No payment is processed here.

Review applications over SSH, without creating a public admin endpoint:

```sh
ssh myotaw-prod 'sudo -u tcso-intake python3 /opt/tcso-intake/review.py --limit 20'
```

For a deletion request, an authorized operator should delete only the verified reference using parameterized SQL, then run `sudo systemctl start tcso-intake-maintenance` to refresh the backup. Do not export records into this repository or post them to public issues.

## Deployment and rollback

Install `intake.py`, `email_verification.py`, `maintenance.py` and `review.py` to `/opt/tcso-intake/`, the three units to `/etc/systemd/system/`, and `nginx-location.conf` as `/etc/nginx/snippets/tcso-intake.conf`. Include that snippet only in the existing myotaw.com TLS server. Validate `sudo nginx -t` before reload; restart the intake service after code updates. Existing Laravel routes remain unchanged. Nginx config backup: `/etc/nginx/sites-available/myotaw.before-tcso-20261108`.

Rollback: remove only the TCSO include from the TLS server, validate/reload nginx, then stop the intake service and timer. Preserve the private database. Frontend Messenger fallback continues to work if intake is unavailable.

Validation: `python3 -m unittest discover -s backend -v` exercises actual HTTP requests, valid submissions, retry deduplication, changed-payload conflicts, invalid input, consent, CORS, rate limits and retention using a temporary database.


## Email verification

POST `/tcso-api/otp/request` sends a six-digit code via Brevo; POST `/tcso-api/otp/verify` exchanges it for an email-bound token required by `/tcso-api/applications`. Codes expire after 10 minutes and five failed guesses. Tokens expire after 30 minutes and can submit one application (idempotent retries allowed). Codes/tokens are hashed at rest. Verification records older than 24 hours are removed by daily maintenance, within 48 hours of creation (request-time cleanup also runs).

Limits: one request per minute, five per hour per email or daily hashed IP, and 200 requests per rolling day for this service. Brevo's shared account quota also applies. SMTP uses STARTTLS on port 587. Secrets live only in root-owned mode-0600 `/etc/tcso-intake.env`, loaded by systemd; never commit them. Required variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`.

Sender: `TCSO Membership <register@tcso.world>`. This is an outbound sender, not a hosted inbox. TCSO has Brevo domain-verification TXT, two DKIM CNAMEs and monitoring DMARC. Myo Taw's existing Zoho mail remains separate. AWS IP 13.215.170.228 is authorized in Brevo; blocking unknown IPs remains enabled. The TCSO SMTP key expires 8 November 2027 and may expire after 90 days of inactivity; renew operationally before expiry.

Tests mock SMTP and cover OTP expiry, attempt limits, email binding, token replay and required server-side verification. No real email is sent by the test suite.

OTP messages include an inline-styled HTML theme and a plain-text alternative. The registration link includes the challenge ID and email in its URL fragment to resume verification in another tab/device. No OTP or verification token is embedded. The browser removes that fragment after reading it. Applicants still enter the code; other application fields must be entered in the new tab. The Messenger handoff copies the reviewed message, including its saved reference, and opens the Page chat. It cannot prefill or send a visitor message through a standard m.me URL. No additional AWS compute resource is provisioned; the service shares the existing Myo Taw host and its resource/bandwidth allowance.
