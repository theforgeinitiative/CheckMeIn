"""Read-only JSON API for other TFI systems (e.g. the member portal).

Authenticated with the same bearer token as /sync (`sync.token`). With no
token configured every request is refused.
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
        if cherrypy.request.method != "GET":
            raise cherrypy.HTTPError(405, "Method Not Allowed")
        self._check_auth()
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

        visits = [
            {
                # Stable across Fix Data edits, which rewrite start (and so
                # visitKey); Fix Data and /sync already rely on rowid too.
                "id": rowid,
                # Same key format the volunteer pilot used ("barcode|start"),
                # so review decisions made there still line up.
                "visitKey": f"{barcode}|{start}",
                "start": start.replace(tzinfo=_SERVER_TZ).isoformat(),
                "leave": leave.replace(tzinfo=_SERVER_TZ).isoformat(),
                "minutes": int((leave - start).total_seconds() // 60),
                "status": status,
            }
            for rowid, start, leave, status in rows
        ]
        cherrypy.response.headers["Content-Type"] = "application/json"
        return json.dumps({"visits": visits}).encode()
