"""JSON API for other TFI systems (e.g. the member portal).

Authenticated with the same bearer token as /sync (`sync.token`). With no
token configured every request is refused. Callers decide which members
they may act for; this API trusts the barcode it is given.
"""
import datetime
import hmac
import json
import pathlib
import zoneinfo

import cherrypy

from webBase import WebBase

try:
    _SERVER_TZ = zoneinfo.ZoneInfo(pathlib.Path("/etc/timezone").read_text().strip())
except Exception:
    _SERVER_TZ = zoneinfo.ZoneInfo("America/New_York")

DEFAULT_DAYS = 30
MAX_DAYS = 366


class WebApi(WebBase):
    def _check_auth(self):
        expected = cherrypy.config.get("sync.token", "")
        auth_header = cherrypy.request.headers.get("Authorization", "")
        supplied = auth_header[7:] if auth_header.startswith("Bearer ") else ""
        if not expected or not hmac.compare_digest(supplied, expected):
            cherrypy.response.headers["WWW-Authenticate"] = 'Bearer realm="api"'
            raise cherrypy.HTTPError(401, "Unauthorized")

    @cherrypy.expose
    def visits(self, barcode=None, since=None):
        """Completed visits (checked out, or closed by "Forgot") for one
        member, newest first. In-progress visits are left out until the
        member checks out."""
        self._require_method("GET")
        if not barcode:
            raise cherrypy.HTTPError(400, "barcode is required")

        today = datetime.date.today()
        if since:
            try:
                since_date = datetime.date.fromisoformat(since)
            except ValueError:
                raise cherrypy.HTTPError(400, "since must be YYYY-MM-DD")
        else:
            since_date = today - datetime.timedelta(days=DEFAULT_DAYS)
        if since_date < today - datetime.timedelta(days=MAX_DAYS):
            raise cherrypy.HTTPError(400, f"since must be within {MAX_DAYS} days")
        since_start = datetime.datetime.combine(since_date, datetime.time.min)

        with self.dbConnect() as db:
            rows = db.execute(
                "SELECT rowid, start, leave, status FROM visits"
                " WHERE barcode == ? AND start >= ? AND status != 'In'"
                " ORDER BY start DESC",
                (barcode, since_start),
            ).fetchall()

        return _json({"visits": [_visit_json(barcode, *row) for row in rows]})

    @cherrypy.expose
    def presence(self, barcode=None):
        """Whether a member is checked in right now, and since when."""
        self._require_method("GET")
        with self.dbConnect() as db:
            self._require_member(db, barcode)
            return _json(_presence(db, barcode))

    @cherrypy.expose
    def checkin(self, barcode=None):
        """Check a member in, like the station does, except that it never
        makes anyone the active keyholder. Checking in twice is harmless."""
        self._require_method("POST")
        with self.dbConnect() as db:
            self._require_member(db, barcode)
            self.engine.visits.checkInMember(db, barcode)
            return _json(_presence(db, barcode))

    @cherrypy.expose
    def checkout(self, barcode=None):
        """Check a member out. The active keyholder is refused: their
        checkout closes the building, which belongs at the station."""
        self._require_method("POST")
        with self.dbConnect() as db:
            self._require_member(db, barcode)
            (keyholder_bc, _) = self.engine.accounts.getActiveKeyholder(db)
            if barcode == keyholder_bc:
                raise cherrypy.HTTPError(
                    409, "Keyholders check out at the station")
            row = db.execute(
                "SELECT rowid FROM visits WHERE barcode == ? AND status == 'In'",
                (barcode,),
            ).fetchone()
            if row is None:
                return _json({"in": False})
            self.engine.visits.checkOutMember(db, barcode)
            visit = db.execute(
                "SELECT rowid, start, leave, status FROM visits WHERE rowid == ?",
                (row[0],),
            ).fetchone()
            return _json({"in": False, "visit": _visit_json(barcode, *visit)})

    def _require_method(self, method):
        if cherrypy.request.method != method:
            raise cherrypy.HTTPError(405, "Method Not Allowed")
        self._check_auth()

    def _require_member(self, db, barcode):
        if not barcode:
            raise cherrypy.HTTPError(400, "barcode is required")
        known = db.execute(
            "SELECT 1 FROM members WHERE barcode == ?", (barcode,)
        ).fetchone()
        if known is None:
            raise cherrypy.HTTPError(404, "Unknown barcode")


def _local(timestamp):
    return timestamp.replace(tzinfo=_SERVER_TZ).isoformat()


def _visit_json(barcode, rowid, start, leave, status):
    return {
        # Stable across Fix Data edits, which rewrite start (and so
        # visitKey); Fix Data and /sync already rely on rowid too.
        "id": rowid,
        # Same key format the volunteer pilot used ("barcode|start"),
        # so review decisions made there still line up.
        "visitKey": f"{barcode}|{start}",
        "start": _local(start),
        "leave": _local(leave),
        "minutes": int((leave - start).total_seconds() // 60),
        "status": status,
    }


def _presence(db, barcode):
    row = db.execute(
        "SELECT start FROM visits WHERE barcode == ? AND status == 'In'",
        (barcode,),
    ).fetchone()
    return {"in": True, "since": _local(row[0])} if row else {"in": False}


def _json(data):
    cherrypy.response.headers["Content-Type"] = "application/json"
    return json.dumps(data).encode()
