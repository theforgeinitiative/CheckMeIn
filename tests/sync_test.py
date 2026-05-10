import json

import CPtest

CSV = (
    '"First Name","Last Name","TFI Barcode for Button","TFI Barcode AUTO",'
    '"TFI Barcode AUTONUM","TFI Display Name for Button","Membership End Date"\n'
    '"Jane","Smith","199001","","199001","Jane S","6/30/2025"\n'
    '"John","Doe","199002","","199002","John D","6/30/2025"\n'
)

AUTH = [('Authorization', 'Bearer testtoken')]


def _multipart(csv_content):
    body = (
        '--x\r\n'
        'Content-Disposition: form-data; name="csvfile"; filename="members.csv"\r\n'
        'Content-Type: text/plain\r\n'
        '\r\n'
        + csv_content +
        '\r\n--x--\r\n'
    )
    headers = [
        ('Content-Type', 'multipart/form-data; boundary=x'),
        ('Content-Length', str(len(body))),
    ]
    return headers, body


class SyncMembersTest(CPtest.CPTest):
    def test_upload(self):
        headers, body = _multipart(CSV)
        self.getPage('/sync/members', AUTH + headers, 'POST', body)
        self.assertStatus('200 OK')
        response = json.loads(self.body)
        self.assertEqual(response['status'], 'ok')
        self.assertIn('2', response['message'])  # "Imported 2 from members.csv"

    def test_no_auth(self):
        headers, body = _multipart(CSV)
        self.getPage('/sync/members', headers, 'POST', body)
        self.assertStatus('401 Unauthorized')

    def test_wrong_token(self):
        headers, body = _multipart(CSV)
        bad_auth = [('Authorization', 'Bearer wrongtoken')]
        self.getPage('/sync/members', bad_auth + headers, 'POST', body)
        self.assertStatus('401 Unauthorized')

    def test_get_not_allowed(self):
        self.getPage('/sync/members', AUTH, 'GET')
        self.assertStatus('405 Method Not Allowed')
