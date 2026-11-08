import http.client
import json
import os
import tempfile
import threading
import unittest
import uuid
os.environ['TCSO_STATE'] = tempfile.mkdtemp(prefix='tcso-test-')
import intake

class IntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = intake.ThreadingHTTPServer(('127.0.0.1', 0), intake.Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
    def request(self, data, origin='https://tcso.world', method='POST'):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        conn.request(method, '/tcso-api/applications', json.dumps(data), {'Origin':origin, 'Content-Type':'application/json'})
        response = conn.getresponse()
        body = response.read()
        status = response.status
        conn.close()
        return status, json.loads(body) if body else {}
    def payload(self):
        return dict(request_id=str(uuid.uuid4()), name='Test Applicant', country='Thailand', plan='paid', consent=True, contact='test@example.com')
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
