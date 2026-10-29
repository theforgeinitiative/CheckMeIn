import datetime
import json
import sqlite3
from unittest.mock import patch
from urllib.parse import quote

import cherrypy

import CPtest

AUTH = [('Authorization', 'Bearer testtoken')]  # the sync token


def _db():
    # The connection's context manager commits on exit.
    return sqlite3.connect('testData/test.db', detect_types=sqlite3.PARSE_DECLTYPES)


class VisitsApiTest(CPtest.CPTest):
    def visits(self, query, headers=AUTH, method='GET'):
        self.getPage('/api/visits' + query, headers, method)
        return json.loads(self.body) if self.status.startswith('200') else None

    def test_returns_completed_visits_for_the_barcode(self):
        data = self.visits('?barcode=100091')
        self.assertStatus('200 OK')
        visits = data['visits']
        # Other test files share this database and may check members in or
        # out, so assert on behavior rather than an exact count.
        self.assertTrue(all(v['status'] != 'In' for v in visits))
        self.assertTrue(all(v['visitKey'].startswith('100091|') for v in visits))
        # Sample data: a finished hour-long visit a week ago.
        week_old = [v for v in visits if v['status'] == 'Out' and v['minutes'] == 60]
        # (Other test files may load the sample data again.)
        self.assertGreaterEqual(len(week_old), 1)
        start = datetime.datetime.fromisoformat(week_old[0]['start'])
        self.assertIsNotNone(start.tzinfo)
        self.assertEqual([v['start'] for v in visits],
                         sorted((v['start'] for v in visits), reverse=True))

    def test_leaves_out_visits_still_in_progress(self):
        # A barcode no other test uses, so this can't disturb them.
        now = datetime.datetime.now()
        with _db() as db:
            db.execute("INSERT INTO visits VALUES (?,?,'199999','In')", (now, now))
        try:
            self.assertEqual(self.visits('?barcode=199999')['visits'], [])
        finally:
            with _db() as db:
                db.execute("DELETE FROM visits WHERE barcode = '199999'")

    def test_visit_key_matches_the_pilot_format(self):
        visit = self.visits('?barcode=100091')['visits'][0]
        naive_start = datetime.datetime.fromisoformat(visit['start']).replace(tzinfo=None)
        self.assertEqual(visit['visitKey'], f'100091|{naive_start}')

    def test_since_excludes_older_visits(self):
        ten_days_ago = datetime.datetime.now() - datetime.timedelta(days=10)
        with _db() as db:
            db.execute("INSERT INTO visits VALUES (?,?,'199998','Out')",
                       (ten_days_ago, ten_days_ago + datetime.timedelta(hours=2)))
        try:
            today = datetime.date.today()
            self.assertEqual(self.visits(f'?barcode=199998&since={today}')['visits'], [])
            earlier = (today - datetime.timedelta(days=11)).isoformat()
            [visit] = self.visits(f'?barcode=199998&since={earlier}')['visits']
            self.assertEqual(visit['minutes'], 120)
        finally:
            with _db() as db:
                db.execute("DELETE FROM visits WHERE barcode = '199998'")

    def test_each_visit_has_an_integer_id(self):
        visits = self.visits('?barcode=100091')['visits']
        self.assertTrue(visits)
        self.assertTrue(all(isinstance(v['id'], int) for v in visits))

    def test_id_survives_a_fix_data_edit(self):
        # Fix Data rewrites start to the whole minute, which changes
        # visitKey; the id must stay the same so review decisions stick.
        start = (datetime.datetime.now() - datetime.timedelta(days=3)).replace(
            hour=14, minute=25, second=7, microsecond=123456)
        with _db() as db:
            db.execute("INSERT INTO visits VALUES (?,?,'199997','Forgot')",
                       (start, start + datetime.timedelta(hours=9)))
        try:
            [before] = self.visits('?barcode=199997')['visits']
            day = start.date().isoformat()
            output = quote(f"{before['id']}!{day} 2:25PM!{day} 3:25PM,")
            with self.patch_session():
                self.getPage(f'/admin/fixed?output={output}')
            [after] = self.visits('?barcode=199997')['visits']
            self.assertEqual(after['id'], before['id'])
            self.assertNotEqual(after['visitKey'], before['visitKey'])
            self.assertEqual(after['minutes'], 60)
        finally:
            with _db() as db:
                db.execute("DELETE FROM visits WHERE barcode = '199997'")

    def test_unknown_barcode_is_empty(self):
        self.assertEqual(self.visits('?barcode=999999')['visits'], [])

    def test_requires_the_sync_token(self):
        self.visits('?barcode=100091', headers=[])
        self.assertStatus('401 Unauthorized')
        self.visits('?barcode=100091', headers=[('Authorization', 'Bearer nope')])
        self.assertStatus('401 Unauthorized')

    def test_refuses_everything_when_no_token_is_configured(self):
        with patch.dict(cherrypy.config, {'sync.token': ''}):
            self.visits('?barcode=100091', headers=[('Authorization', 'Bearer ')])
        self.assertStatus('401 Unauthorized')

    def test_requires_a_barcode(self):
        self.visits('')
        self.assertStatus('400 Bad Request')

    def test_rejects_a_bad_since(self):
        self.visits('?barcode=100091&since=yesterday')
        self.assertStatus('400 Bad Request')
        old = (datetime.date.today() - datetime.timedelta(days=400)).isoformat()
        self.visits(f'?barcode=100091&since={old}')
        self.assertStatus('400 Bad Request')

    def test_is_read_only(self):
        self.visits('?barcode=100091', method='POST')
        self.assertStatus('405 Method Not Allowed')


class PresenceApiTest(CPtest.CPTest):
    interactive = False
    # Barcodes no other test uses; each test adds and removes its own member.
    MEMBER = '199996'
    KEYHOLDER = '199995'

    def setUp(self):
        with _db() as db:
            for bc in (self.MEMBER, self.KEYHOLDER):
                db.execute("INSERT INTO members (barcode, displayName) VALUES (?, ?)",
                           (bc, f'API Test {bc}'))

    def tearDown(self):
        with _db() as db:
            for bc in (self.MEMBER, self.KEYHOLDER):
                db.execute("DELETE FROM visits WHERE barcode = ?", (bc,))
                db.execute("DELETE FROM members WHERE barcode = ?", (bc,))
                db.execute("DELETE FROM accounts WHERE barcode = ?", (bc,))

    def call(self, path, barcode, method='POST', headers=AUTH):
        if method == 'GET':
            self.getPage(f'{path}?barcode={barcode}', headers, 'GET')
        else:
            body = f'barcode={barcode}'
            self.getPage(path, headers + [
                ('Content-Type', 'application/x-www-form-urlencoded'),
                ('Content-Length', str(len(body)))], method, body)
        return json.loads(self.body) if self.status.startswith('200') else None

    def open_visits(self, barcode):
        with _db() as db:
            return db.execute("SELECT COUNT(*) FROM visits WHERE barcode = ? AND status = 'In'",
                              (barcode,)).fetchone()[0]

    def test_presence_starts_out(self):
        self.assertEqual(self.call('/api/presence', self.MEMBER, 'GET'), {'in': False})

    def test_check_in_then_out_records_one_visit(self):
        checked_in = self.call('/api/checkin', self.MEMBER)
        self.assertTrue(checked_in['in'])
        self.assertIsNotNone(datetime.datetime.fromisoformat(checked_in['since']).tzinfo)
        self.assertEqual(self.call('/api/presence', self.MEMBER, 'GET'), checked_in)

        checked_out = self.call('/api/checkout', self.MEMBER)
        self.assertFalse(checked_out['in'])
        visit = checked_out['visit']
        self.assertEqual(visit['status'], 'Out')
        self.assertEqual(visit['start'], checked_in['since'])
        [listed] = self.visits_for(self.MEMBER)
        self.assertEqual(listed, visit)

    def visits_for(self, barcode):
        self.getPage(f'/api/visits?barcode={barcode}', AUTH)
        return json.loads(self.body)['visits']

    def test_checking_in_twice_keeps_one_open_visit(self):
        first = self.call('/api/checkin', self.MEMBER)
        second = self.call('/api/checkin', self.MEMBER)
        self.assertEqual(first, second)
        self.assertEqual(self.open_visits(self.MEMBER), 1)

    def test_checking_out_when_not_in_changes_nothing(self):
        self.assertEqual(self.call('/api/checkout', self.MEMBER), {'in': False})
        self.assertEqual(self.visits_for(self.MEMBER), [])

    def test_unknown_barcode_is_not_found(self):
        for path, method in (('/api/presence', 'GET'), ('/api/checkin', 'POST'),
                             ('/api/checkout', 'POST')):
            self.call(path, '999999', method)
            self.assertStatus('404 Not Found')
        self.assertEqual(self.open_visits('999999'), 0)

    def test_check_in_never_makes_anyone_keyholder(self):
        with _db() as db:
            db.execute("INSERT INTO accounts (user, barcode, role) VALUES ('apitestkh', ?, 16)",
                       (self.KEYHOLDER,))
            active = [r[0] for r in db.execute(
                "SELECT barcode FROM accounts WHERE activeKeyholder = 1")]
            db.execute("UPDATE accounts SET activeKeyholder = 0")
        try:
            self.call('/api/checkin', self.KEYHOLDER)
            with _db() as db:
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM accounts WHERE activeKeyholder = 1").fetchone()[0], 0)
        finally:
            with _db() as db:
                for bc in active:
                    db.execute("UPDATE accounts SET activeKeyholder = 1 WHERE barcode = ?", (bc,))

    def test_active_keyholder_cannot_check_out(self):
        with _db() as db:
            db.execute("INSERT INTO accounts (user, barcode, role) VALUES ('apitestkh', ?, 16)",
                       (self.KEYHOLDER,))
            active = [r[0] for r in db.execute(
                "SELECT barcode FROM accounts WHERE activeKeyholder = 1")]
            db.execute("UPDATE accounts SET activeKeyholder = 0")
            db.execute("UPDATE accounts SET activeKeyholder = 1 WHERE barcode = ?",
                       (self.KEYHOLDER,))
        try:
            self.call('/api/checkin', self.KEYHOLDER)
            self.call('/api/checkin', self.MEMBER)
            self.call('/api/checkout', self.KEYHOLDER)
            self.assertStatus('409 Conflict')
            self.assertInBody('Keyholders check out at the station')
            # Nobody was closed out.
            self.assertEqual(self.open_visits(self.KEYHOLDER), 1)
            self.assertEqual(self.open_visits(self.MEMBER), 1)
        finally:
            with _db() as db:
                db.execute("UPDATE accounts SET activeKeyholder = 0")
                for bc in active:
                    db.execute("UPDATE accounts SET activeKeyholder = 1 WHERE barcode = ?", (bc,))

    def test_requires_the_sync_token(self):
        for path, method in (('/api/presence', 'GET'), ('/api/checkin', 'POST'),
                             ('/api/checkout', 'POST')):
            self.call(path, self.MEMBER, method, headers=[])
            self.assertStatus('401 Unauthorized')
        self.assertEqual(self.open_visits(self.MEMBER), 0)

    def test_writes_must_be_posts(self):
        for path in ('/api/checkin', '/api/checkout'):
            self.call(path, self.MEMBER, 'GET')
            self.assertStatus('405 Method Not Allowed')
        self.assertEqual(self.open_visits(self.MEMBER), 0)
        self.call('/api/presence', self.MEMBER, 'POST')
        self.assertStatus('405 Method Not Allowed')

    def test_requires_a_barcode(self):
        for path, method in (('/api/presence', 'GET'), ('/api/checkin', 'POST'),
                             ('/api/checkout', 'POST')):
            self.call(path, '', method)
            self.assertStatus('400 Bad Request')
