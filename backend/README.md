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

Install `intake.py`, `maintenance.py` and `review.py` to `/opt/tcso-intake/`, the three units to `/etc/systemd/system/`, and `nginx-location.conf` as `/etc/nginx/snippets/tcso-intake.conf`. Include that snippet only in the existing myotaw.com TLS server. Validate `sudo nginx -t` before reload; restart the intake service after code updates. Existing Laravel routes remain unchanged. Nginx config backup: `/etc/nginx/sites-available/myotaw.before-tcso-20261108`.

Rollback: remove only the TCSO include from the TLS server, validate/reload nginx, then stop the intake service and timer. Preserve the private database. Frontend Messenger fallback continues to work if intake is unavailable.

Validation: `python3 -m unittest discover -s backend -v` exercises actual HTTP requests, valid submissions, retry deduplication, changed-payload conflicts, invalid input, consent, CORS, rate limits and retention using a temporary database.
