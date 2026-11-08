"""TCSO membership intake. No external packages; private SQLite storage."""
import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import email_verification as verification

STATE = Path(os.environ.get('TCSO_STATE', '/var/lib/tcso-intake'))
ORIGINS = {'https://tcso.world', 'https://www.tcso.world', 'https://thiha-lynn.github.io'}

def database():
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    db = sqlite3.connect(STATE / 'applications.sqlite3', timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS applications (request_id TEXT PRIMARY KEY, reference TEXT UNIQUE, created INTEGER, payload TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS rate_limits (client TEXT, created INTEGER)')
    return db

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Do not log applicant details or request bodies.

    def respond(self, status, data=None):
        self.send_response(status)
        origin = self.headers.get('Origin', '')
        if origin in ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('X-Content-Type-Options', 'nosniff')
        body = b'' if status == 204 else json.dumps(data or {}, ensure_ascii=False).encode()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.respond(204 if self.headers.get('Origin') in ORIGINS else 403)

    def do_GET(self):
        self.respond(405, {'error': 'Use the membership form to submit an application.'})

    def do_POST(self):
        if self.path not in ('/tcso-api/applications', '/tcso-api/otp/request', '/tcso-api/otp/verify'):
            return self.respond(404)
        if self.headers.get('Origin') not in ORIGINS:
            return self.respond(403, {'error': 'Unrecognized application origin.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.respond(415, {'error': 'JSON required.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 8192:
                return self.respond(413, {'error': 'Application too large.'})
            self.connection.settimeout(10)
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError()
            client = hashlib.sha256((self.headers.get('X-Real-IP', self.client_address[0]) + time.strftime('%Y-%m-%d', time.gmtime())).encode()).hexdigest()
            if self.path == '/tcso-api/otp/request':
                return self.respond(200, verification.request_code(database, data, client))
            if self.path == '/tcso-api/otp/verify':
                return self.respond(200, verification.verify_code(database, data))
            request_id = str(uuid.UUID(data.get('request_id', '')))
            if data.get('consent') is not True or data.get('website'):
                raise ValueError()
            clean = {}
            for key, limit in [('name', 80), ('country', 80), ('contact', 160), ('coordinator', 80), ('currency', 80), ('payment_method', 100)]:
                value = data.get(key, '')
                if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 for c in value):
                    raise ValueError()
                clean[key] = value.strip()
            if not clean['name'] or not clean['country'] or data.get('plan') not in ('free', 'paid'):
                raise ValueError()
            clean['contact'] = verification.normalize_email(clean['contact'])
            clean.update(plan=data['plan'], consent=True, privacy_version='2026-11-08-otp', email_verified=True, membership_fee_usd=30 if data['plan'] == 'paid' else 0, membership_billing='one-time')
            if clean['plan'] == 'free':
                clean['currency'] = clean['payment_method'] = ''
        except verification.VerificationError as error:
            return self.respond(error.status, {'error':error.message})
        except sqlite3.Error:
            return self.respond(503, {'error':'Verification is temporarily unavailable.'})
        except (ValueError, TypeError, AttributeError, TimeoutError):
            return self.respond(422, {'error': 'Please check your name, country, email, plan and consent.'})
        try:
            now = int(time.time())
            # Proxy sets this header; the service is bound to loopback only.
            client = hashlib.sha256((self.headers.get('X-Real-IP', self.client_address[0]) + time.strftime('%Y-%m-%d', time.gmtime())).encode()).hexdigest()
            encoded = json.dumps(clean, ensure_ascii=False, sort_keys=True)
            with database() as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('DELETE FROM applications WHERE created < ?', (now - 90 * 86400,))
                db.execute('DELETE FROM rate_limits WHERE created < ?', (now - 3600,))
                verification_id = verification.authorize(db, clean['contact'], data.get('verification_token'), request_id)
                existing = db.execute('SELECT reference, payload FROM applications WHERE request_id = ?', (request_id,)).fetchone()
                if existing:
                    if existing[1] != encoded:
                        return self.respond(409, {'error': 'Please review the changed application again.'})
                    return self.respond(200, {'reference': existing[0], 'status': 'received'})
                if db.execute('SELECT COUNT(*) FROM rate_limits WHERE client = ?', (client,)).fetchone()[0] >= 10:
                    return self.respond(429, {'error': 'Too many submissions. Please try later or use Messenger.'})
                reference = 'TCSO-' + uuid.uuid4().hex[:16].upper()
                db.execute('UPDATE email_codes SET used_request=? WHERE id=?', (request_id, verification_id))
                db.execute('INSERT INTO applications VALUES (?, ?, ?, ?)', (request_id, reference, now, encoded))
                db.execute('INSERT INTO rate_limits VALUES (?, ?)', (client, now))
            self.respond(201, {'reference': reference, 'status': 'received'})
        except verification.VerificationError as error:
            self.respond(error.status, {'error':error.message})
        except sqlite3.Error:
            self.respond(503, {'error': 'Intake is temporarily unavailable. Please use Messenger.'})

if __name__ == '__main__':
    os.umask(0o077)
    with database() as db:
        db.execute('DELETE FROM applications WHERE created < ?', (int(time.time()) - 90 * 86400,))
    ThreadingHTTPServer(('127.0.0.1', int(os.environ.get('TCSO_PORT', '8766'))), Handler).serve_forever()
