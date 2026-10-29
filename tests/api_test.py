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
