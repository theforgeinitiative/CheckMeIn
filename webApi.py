"""JSON API for other TFI systems (e.g. the member portal).

Authenticated with the same bearer token as /sync (`sync.token`). With no
token configured every request is refused.

Endpoints:

GET /api/visits?barcode=...&since=YYYY-MM-DD
    A member's completed visits. Read-only.

GET /api/roles
    200 {"roles": {"keyholder": [barcode, ...], "certifier": [...],
                   "coach": [...], "steward": [...]}}
    Every account with the role, current member or not.

POST /api/roles   (Content-Type: application/json)
    {"barcode": "100091", "role": "keyholder", "enabled": true}
    Sets or clears that one role; every other bit, including admin, is
    kept. role is one of keyholder, certifier, coach, steward; admin can't
    be changed here. Only a real change is saved (which emails ops and
    syncs roles to BigQuery).
    200 {"barcode": "100091", "roles": ["keyholder", ...], "changed": true}
    400 bad body, 404 no account for the barcode.
"""
import datetime
import hmac
import json
import pathlib
import zoneinfo

import cherrypy

from accounts import Role
from webBase import WebBase
from webSync import try_sync_roles

try:
    _SERVER_TZ = zoneinfo.ZoneInfo(pathlib.Path("/etc/timezone").read_text().strip())
except Exception:
    _SERVER_TZ = zoneinfo.ZoneInfo("America/New_York")

DEFAULT_DAYS = 30
MAX_DAYS = 366

# The roles the portal manages. ADMIN is deliberately absent so it can never
# be set or cleared through the API.
ROLE_BITS = {
    "keyholder": Role.KEYHOLDER,
    "certifier": Role.SHOP_CERTIFIER,
    "coach": Role.COACH,
    "steward": Role.SHOP_STEWARD,
}


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

    @cherrypy.expose
    def roles(self, **_params):
        """GET lists who holds each role; POST sets or clears one role for
        one account. See the module docstring for the contract."""
        method = cherrypy.request.method
        if method not in ("GET", "POST"):
            raise cherrypy.HTTPError(405, "Method Not Allowed")
        self._check_auth()
        body = self._list_roles() if method == "GET" else self._set_role()
        cherrypy.response.headers["Content-Type"] = "application/json"
        return json.dumps(body).encode()

    def _list_roles(self):
        roles = {name: [] for name in ROLE_BITS}
        with self.dbConnect() as db:
            rows = db.execute(
                "SELECT barcode, role FROM accounts WHERE role != 0"
                " ORDER BY barcode"
            ).fetchall()
        for barcode, value in rows:
            for name, bit in ROLE_BITS.items():
                if value & bit:
                    roles[name].append(barcode)
        return {"roles": roles}

    def _set_role(self):
        try:
            payload = json.loads(cherrypy.request.body.read() or b"")
        except ValueError:
            raise cherrypy.HTTPError(
                400, "body must be JSON (Content-Type: application/json)")
        if not isinstance(payload, dict):
            raise cherrypy.HTTPError(400, "body must be a JSON object")
        barcode = payload.get("barcode")
        role = payload.get("role")
        enabled = payload.get("enabled")
        if not isinstance(barcode, str) or not barcode:
            raise cherrypy.HTTPError(400, "barcode must be a non-empty string")
        if role not in ROLE_BITS:
            raise cherrypy.HTTPError(
                400, "role must be one of " + ", ".join(ROLE_BITS))
        if not isinstance(enabled, bool):
            raise cherrypy.HTTPError(400, "enabled must be true or false")

        bit = ROLE_BITS[role]
        with self.dbConnect() as db:
            row = db.execute(
                "SELECT role FROM accounts WHERE barcode = ?", (barcode,)
            ).fetchone()
            if row is None:
                raise cherrypy.HTTPError(404, "No account for that barcode")
            old_value = row[0] or 0
            new_value = (old_value | bit) if enabled else (old_value & ~bit)
            changed = new_value != old_value
            if changed:
                self.engine.accounts.changeRole(db, barcode, Role(new_value))

        if changed:
            # The role change is already committed, so a BigQuery hiccup
            # shouldn't fail the request.
            try_sync_roles(self.dbConnect)

        return {
            "barcode": barcode,
            "roles": [name for name, b in ROLE_BITS.items() if new_value & b],
            "changed": changed,
        }
