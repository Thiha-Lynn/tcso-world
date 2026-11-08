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
from urllib.parse import urlencode
from html import escape
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

def render_code_html(code, resume_url="https://tcso.world/membership/#apply"):
    if not re.fullmatch(r'[0-9]{6}', code):
        raise ValueError('A six-digit code is required')
    resume_url = escape(resume_url, quote=True)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Your TCSO verification code</title></head>
<body style="margin:0;padding:0;background:#eef0eb;color:#18362c;font-family:Arial,Helvetica,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">Verify your email to take the next step with TCSO. Your code expires in 10 minutes.</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef0eb;"><tr><td align="center" style="padding:28px 12px;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:580px;background:#fffdf7;border:1px solid #dfd8c8;border-radius:18px;overflow:hidden;">
<tr><td style="padding:28px 30px;background:#0c202d;border-bottom:3px solid #d6b771;">
<table role="presentation" cellspacing="0" cellpadding="0"><tr><td width="66"><img src="https://tcso.world/assets/tcso-emblem.jpg" alt="TCSO emblem" width="52" height="52" style="display:block;border-radius:50%;border:1px solid #d6b771;"></td><td style="color:#f6e2ae;font-size:26px;letter-spacing:4px;">TCSO<br><span style="font-size:10px;letter-spacing:1px;color:#dce4e6;">THIRD-COUNTRY SUPPORTERS ORGANIZATION</span></td></tr></table>
</td></tr>
<tr><td style="padding:32px 30px 12px;"><p style="margin:0 0 14px;font-size:11px;font-weight:bold;letter-spacing:2px;color:#85662f;">YOUR COMMUNITY STARTS HERE</p><h1 style="margin:0 0 16px;font-family:Georgia,serif;font-size:32px;line-height:1.25;color:#0c202d;">One small step.<br>A shared future.</h1><p style="margin:0;font-size:16px;line-height:1.8;">Use this code in your TCSO application to verify your email.</p><p lang="my" style="margin:8px 0 18px;font-size:14px;line-height:1.9;">အီးမေးလ်အတည်ပြုရန် အောက်ပါကုဒ်ကို ဖွင့်ထားသော TCSO လျှောက်လွှာတွင် ထည့်ပါ။</p></td></tr>
<tr><td style="padding:0 30px 24px;"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5e7bd;border:1px solid #d6b771;border-radius:12px;"><tr><td align="center" style="padding:24px 8px;"><p style="margin:0 0 10px;font-size:11px;letter-spacing:2px;color:#624b22;">YOUR VERIFICATION CODE</p><div style="font-family:Consolas,Monaco,monospace;font-size:36px;letter-spacing:6px;font-weight:bold;color:#0c202d;white-space:nowrap;">{code}</div><p style="margin:12px 0 0;font-size:13px;color:#624b22;">Valid for 10 minutes · Select code to copy</p></td></tr></table></td></tr>
<tr><td style="padding:0 30px 28px;"><p style="font-size:14px;line-height:1.8;margin:0 0 16px;"><strong>1.</strong> Open the verification link or return to your application.<br><strong>2.</strong> Enter the six digits and select Verify code.<br><strong>3.</strong> Review your details, submit, then continue in Messenger.</p><p style="font-size:13px;line-height:1.8;margin:0 0 20px;">You can continue in a new tab or on another device. Open the secure registration link below, then enter this code.</p><a href="{resume_url}" style="display:inline-block;background:#0c202d;color:#f6e2ae;text-decoration:none;font-size:14px;font-weight:bold;padding:16px 24px;border-radius:28px;">Continue verification &rarr;</a><p style="font-size:12px;line-height:1.8;color:#617168;margin:22px 0 0;">Enter this code only at <strong>tcso.world</strong>. Never share it in Messenger. Verification does not enroll you or charge a fee. If you did not request it, simply ignore this email.</p></td></tr>
<tr><td style="padding:22px 30px;background:#eaf0e8;border-top:1px solid #dce2d6;"><p style="font-family:Georgia,serif;font-size:17px;color:#244837;margin:0 0 10px;">Bridging borders. Building futures. Together.</p><p style="font-size:12px;line-height:1.8;margin:0;color:#536558;">TCSO membership verification · This address sends automated emails.<br>Need help? <a href="https://m.me/TCSODL" style="color:#244837;">Contact TCSO on Messenger</a> · <a href="https://tcso.world" style="color:#244837;">Visit our website</a></p></td></tr>
</table></td></tr></table></body></html>'''

def send_code(email, code, challenge=None):
    user=os.environ.get('SMTP_USERNAME',''); password=os.environ.get('SMTP_PASSWORD','')
    if not user or not password: raise VerificationError(503,'Email verification is temporarily unavailable. Please try again later.')
    resume_url = "https://tcso.world/membership/#" + urlencode({"verify":challenge,"email":email}) if challenge else "https://tcso.world/membership/#apply"
    msg=EmailMessage()
    msg['Subject']='Your TCSO verification code'
    msg['From']=os.environ.get('SMTP_FROM','TCSO Membership <register@tcso.world>')
    msg['To']=email
    msg.set_content(f'Your TCSO membership verification code is: {code}\n\nThis code expires in 10 minutes. Enter it only at https://tcso.world/membership/. Never share this code.\nContinue in any tab: {resume_url}\n\nVerifying your email does not enroll you or charge a membership fee. If you did not request this code, ignore this email.\n\nTCSO — Third-Country Supporters Organization\nhttps://tcso.world')
    msg.add_alternative(render_code_html(code, resume_url), subtype='html')
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
    try: send_code(email,code,challenge)
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
