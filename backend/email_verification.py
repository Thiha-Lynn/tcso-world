"""Short-lived email codes and single-application verification tokens."""
import hashlib
import hmac
import os
import re
import secrets
import smtplib
import ssl
import time
import uuid
from email.message import EmailMessage

class VerificationError(Exception):
    def __init__(self, status, message): self.status, self.message = status, message

def normalize_email(value):
    if not isinstance(value,str): raise VerificationError(422,'Enter a valid email address.')
    email=value.strip().lower()
    if len(email)>160 or not re.fullmatch(r'[^\s@\x00-\x1f]+@[^\s@\x00-\x1f]+\.[^\s@\x00-\x1f]+',email):
        raise VerificationError(422,'Enter a valid email address.')
    return email

def schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS email_codes (id TEXT PRIMARY KEY, email TEXT, digest TEXT, salt TEXT, created INTEGER, attempts INTEGER DEFAULT 0, token_hash TEXT, verified INTEGER, used_request TEXT, sent INTEGER DEFAULT 0, client TEXT)')

def send_code(email, code):
    user=os.environ.get('SMTP_USERNAME',''); password=os.environ.get('SMTP_PASSWORD','')
    if not user or not password: raise VerificationError(503,'Email verification is temporarily unavailable. Please try again later.')
    msg=EmailMessage()
    msg['Subject']='Your TCSO verification code'
    msg['From']=os.environ.get('SMTP_FROM','TCSO Membership <register@tcso.world>')
    msg['To']=email
    msg.set_content(f'Your TCSO membership verification code is: {code}\n\nThis code expires in 10 minutes. Enter it only at https://tcso.world/membership/. Never share this code.\n\nVerifying your email does not enroll you or charge a membership fee. If you did not request this code, ignore this email.\n\nTCSO — Third-Country Supporters Organization\nhttps://tcso.world')
    with smtplib.SMTP(os.environ.get('SMTP_HOST','smtp-relay.brevo.com'),int(os.environ.get('SMTP_PORT','587')),timeout=12) as smtp:
        smtp.ehlo(); smtp.starttls(context=ssl.create_default_context()); smtp.ehlo()
        smtp.login(user,password); smtp.send_message(msg)

def request_code(database,data,client):
    email=normalize_email(data.get('email'))
    if data.get('email_consent') is not True or data.get('website'):
        raise VerificationError(422,'Agree to receive the verification email before continuing.')
    now=int(time.time()); challenge=str(uuid.uuid4()); salt=secrets.token_hex(16); code=f'{secrets.randbelow(1000000):06d}'
    digest=hashlib.sha256((salt+code).encode()).hexdigest()
    with database() as db:
        db.execute('BEGIN IMMEDIATE'); schema(db)
        db.execute('DELETE FROM email_codes WHERE created < ?', (now-86400,))
        recent=db.execute('SELECT max(created), count(*) FROM email_codes WHERE created>? AND (email=? OR client=?)',(now-3600,email,client)).fetchone()
        total=db.execute('SELECT count(*) FROM email_codes WHERE created>?',(now-86400,)).fetchone()[0]
        if (recent[0] and recent[0]>now-60) or recent[1]>=5 or total>=200:
            raise VerificationError(429,'Please wait before requesting another code. You can request up to 5 codes per hour.')
        db.execute('INSERT INTO email_codes (id,email,digest,salt,created,client) VALUES (?,?,?,?,?,?)',(challenge,email,digest,salt,now,client))
    try: send_code(email,code)
    except (smtplib.SMTPException,OSError):
        raise VerificationError(503,'We could not send your code. Please wait a minute and try again.') from None
    with database() as db:
        db.execute('UPDATE email_codes SET sent=1 WHERE id=?',(challenge,))
    return {'challenge_id':challenge,'expires_in':600,'resend_after':60}

def verify_code(database,data):
    email=normalize_email(data.get('email')); challenge=data.get('challenge_id'); code=data.get('code')
    if not isinstance(challenge,str) or not isinstance(code,str) or not re.fullmatch(r'\d{6}',code):
        raise VerificationError(422,'Enter the six-digit code from your email.')
    now=int(time.time()); token=secrets.token_urlsafe(32); error=None
    with database() as db:
        db.execute('BEGIN IMMEDIATE'); schema(db)
        row=db.execute('SELECT email,digest,salt,created,attempts,verified,sent FROM email_codes WHERE id=?',(challenge,)).fetchone()
        if not row or row[0]!=email or row[3]<now-600 or row[4]>=5 or row[5] or not row[6]:
            error='This code expired or is no longer valid. Request a new code.'
        elif not hmac.compare_digest(row[1],hashlib.sha256((row[2]+code).encode()).hexdigest()):
            db.execute('UPDATE email_codes SET attempts=attempts+1 WHERE id=?',(challenge,))
            error='That code is incorrect. Check your email and try again.'
        else:
            db.execute('UPDATE email_codes SET token_hash=?,verified=?,digest=?,salt=? WHERE id=?',(hashlib.sha256(token.encode()).hexdigest(),now,'','',challenge))
    if error: raise VerificationError(422,error)
    return {'verification_token':token,'expires_in':1800}

def authorize(db,email,token,request_id):
    if not isinstance(token,str) or len(token)>128: raise VerificationError(403,'Verify your email before submitting.')
    schema(db)
    row=db.execute('SELECT id,email,verified,used_request FROM email_codes WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
    if not row or row[1]!=email or not row[2] or row[2]<int(time.time())-1800 or (row[3] and row[3]!=request_id):
        raise VerificationError(403,'Email verification expired or was already used. Please verify again.')
    return row[0]
