import http.client
import json
import os
import tempfile
import threading
import unittest
import uuid
from unittest.mock import patch
import time
os.environ['TCSO_STATE'] = tempfile.mkdtemp(prefix='tcso-test-')
import intake
import email_verification as verification
OUTBOX = {}
verification.send_code = lambda email, code: OUTBOX.update({email: code})

class IntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = intake.ThreadingHTTPServer(('127.0.0.1', 0), intake.Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
    def request(self, data, origin='https://tcso.world', method='POST', path='/tcso-api/applications', client='test-client'):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        conn.request(method, path, json.dumps(data), {'Origin':origin, 'Content-Type':'application/json','X-Real-IP':client})
        response = conn.getresponse()
        body = response.read()
        status = response.status
        conn.close()
        return status, json.loads(body) if body else {}
    def payload(self):
        email = uuid.uuid4().hex+'@example.com'
        challenge = verification.request_code(intake.database, {'email':email,'email_consent':True}, uuid.uuid4().hex)
        token = verification.verify_code(intake.database, {'email':email,'challenge_id':challenge['challenge_id'],'code':OUTBOX[email]})['verification_token']
        return dict(verification_token=token,request_id=str(uuid.uuid4()), name='Test Applicant', country='Thailand', plan='paid', consent=True, contact=email)
    def test_save_and_idempotent_retry(self):
        data = self.payload()
        status, result = self.request(data)
        self.assertEqual(status, 201)
        self.assertEqual(self.request(data), (200, result))
        data['name'] = 'Changed'
        self.assertEqual(self.request(data)[0], 409)
    def test_validation_and_origin(self):
        for field, value in [('consent',False), ('name',' '), ('plan','other'), ('contact','not-an-email'), ('website','spam'), ('country',[]), ('request_id','invalid')]:
            data = self.payload(); data[field] = value
            self.assertEqual(self.request(data)[0], 422, field)
        self.assertEqual(self.request(self.payload(), origin='https://evil.example')[0],403)
        self.assertEqual(self.request({}, method='GET')[0],405)
        self.assertEqual(self.request({}, method='OPTIONS')[0],204)
    def test_email_code_lifecycle(self):
        email=uuid.uuid4().hex+'@example.com'; client=uuid.uuid4().hex
        code_request={'email':email,'email_consent':True}
        status,result=self.request(code_request,path='/tcso-api/otp/request',client=client)
        self.assertEqual(status,200)
        self.assertEqual(self.request(code_request,path='/tcso-api/otp/request',client=client)[0],429)
        verification_request={'email':email,'challenge_id':result['challenge_id'],'code':OUTBOX[email]}
        wrong=dict(verification_request,code='000000' if OUTBOX[email]!='000000' else '111111')
        self.assertEqual(self.request(wrong,path='/tcso-api/otp/verify')[0],422)
        status,verified=self.request(verification_request,path='/tcso-api/otp/verify')
        self.assertEqual(status,200)
        self.assertEqual(self.request(verification_request,path='/tcso-api/otp/verify')[0],422)
        data=dict(request_id=str(uuid.uuid4()),name='OTP Test',country='Thailand',plan='free',contact=email,consent=True,verification_token=verified['verification_token'])
        self.assertEqual(self.request(dict(data,contact='other@example.com'))[0],403)
        self.assertEqual(self.request(data)[0],201)
        self.assertEqual(self.request(data)[0],200)
        data['request_id']=str(uuid.uuid4())
        self.assertEqual(self.request(data)[0],403)
    def test_missing_verification_rejected(self):
        data=self.payload();data.pop('verification_token')
        self.assertEqual(self.request(data)[0],403)
    def test_email_attempt_limit_and_expiry(self):
        email=uuid.uuid4().hex+'@example.com'
        result=verification.request_code(intake.database,{'email':email,'email_consent':True},uuid.uuid4().hex)
        good=OUTBOX[email]; bad='000000' if good!='000000' else '111111'
        data={'email':email,'challenge_id':result['challenge_id'],'code':bad}
        for _ in range(5):self.assertEqual(self.request(data,path='/tcso-api/otp/verify')[0],422)
        data['code']=good
        self.assertEqual(self.request(data,path='/tcso-api/otp/verify')[0],422)
        email2=uuid.uuid4().hex+'@example.com'
        result=verification.request_code(intake.database,{'email':email2,'email_consent':True},uuid.uuid4().hex)
        with intake.database() as db:db.execute('UPDATE email_codes SET created=? WHERE id=?',(int(time.time())-601,result['challenge_id']))
        self.assertEqual(self.request({'email':email2,'challenge_id':result['challenge_id'],'code':OUTBOX[email2]},path='/tcso-api/otp/verify')[0],422)
    def test_rate_limit_and_retention(self):
        with intake.database() as db:
            db.execute('DELETE FROM rate_limits')
            db.execute('INSERT INTO applications VALUES (?, ?, ?, ?)', ('old','OLD',1,'{}'))
        for _ in range(10):
            self.assertEqual(self.request(self.payload())[0],201)
        self.assertEqual(self.request(self.payload())[0],429)
        with intake.database() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM applications WHERE reference = ?', ('OLD',)).fetchone()[0],0)
            db.execute('DELETE FROM rate_limits')

if __name__ == '__main__': unittest.main()
