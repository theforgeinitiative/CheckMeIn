import json
import cherrypy
from webBase import WebBase
from google.cloud import bigquery
from google.oauth2 import service_account


class WebSync(WebBase):
    def _check_auth(self):
        expected = cherrypy.config.get("sync.token", "")
        auth_header = cherrypy.request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header[7:] != expected:
            cherrypy.response.headers["WWW-Authenticate"] = 'Bearer realm="sync"'
            raise cherrypy.HTTPError(401, "Unauthorized")

    def _get_bq_client(self):
        project = cherrypy.config.get("bigquery.project", "")
        creds_path = cherrypy.config.get("bigquery.credentials", "")
        if creds_path:
            creds = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/bigquery"],
            )
            return bigquery.Client(credentials=creds, project=project)
        return bigquery.Client(project=project)

    def _upload(self, table_name, rows, schema):
        client = self._get_bq_client()
        dataset = cherrypy.config.get("bigquery.dataset", "")
        table_ref = f"{client.project}.{dataset}.{table_name}"
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            schema=schema,
        )
        job = client.load_table_from_json(rows, table_ref, job_config=job_config)
        job.result()
        return len(rows)

    def _json_response(self, rows_uploaded):
        cherrypy.response.headers["Content-Type"] = "application/json"
        return json.dumps({"status": "ok", "rows_uploaded": rows_uploaded}).encode()

    def _require_post(self):
        if cherrypy.request.method != "POST":
            raise cherrypy.HTTPError(405, "Method Not Allowed")

    def _load_visits(self):
        with self.dbConnect() as db:
            cursor = db.execute(
                "SELECT rowid, start, leave, barcode, status FROM visits"
            )
            return [
                {
                    "rowid":   row[0],
                    "start":   row[1].isoformat() if row[1] else None,
                    "leave":   row[2].isoformat() if row[2] else None,
                    "barcode": row[3],
                    "status":  row[4],
                }
                for row in cursor.fetchall()
            ]

    def _load_guests(self):
        with self.dbConnect() as db:
            cursor = db.execute(
                "SELECT guest_id, displayName, email, firstName, lastName,"
                "       whereFound, status, newsletter FROM guests"
            )
            return [
                {
                    "guest_id":    row[0],
                    "displayName": row[1],
                    "email":       row[2],
                    "firstName":   row[3],
                    "lastName":    row[4],
                    "whereFound":  row[5],
                    "status":      row[6],
                    "newsletter":  row[7],
                }
                for row in cursor.fetchall()
            ]

    def _load_unlocks(self):
        with self.dbConnect() as db:
            cursor = db.execute(
                "SELECT time, location, barcode FROM unlocks"
            )
            return [
                {
                    "time":     row[0].isoformat() if row[0] else None,
                    "location": row[1],
                    "barcode":  row[2],
                }
                for row in cursor.fetchall()
            ]

    def _load_certifications(self):
        with self.dbConnect() as db:
            cursor = db.execute(
                "SELECT c.user_id, c.tool_id, t.name, c.certifier_id, c.date, c.level"
                " FROM certifications c"
                " INNER JOIN tools t ON t.id = c.tool_id"
            )
            return [
                {
                    "user_id":      row[0],
                    "tool_id":      row[1],
                    "tool_name":    row[2],
                    "certifier_id": row[3],
                    "date":         row[4].isoformat() if row[4] else None,
                    "level":        row[5],
                }
                for row in cursor.fetchall()
            ]

    @cherrypy.expose
    def index(self):
        self._require_post()
        self._check_auth()
        results = {
            "visits": self._upload(
                "visits",
                self._load_visits(),
                [
                    bigquery.SchemaField("rowid",   "INTEGER"),
                    bigquery.SchemaField("start",   "TIMESTAMP"),
                    bigquery.SchemaField("leave",   "TIMESTAMP"),
                    bigquery.SchemaField("barcode", "STRING"),
                    bigquery.SchemaField("status",  "STRING"),
                ],
            ),
            "guests": self._upload(
                "guests",
                self._load_guests(),
                [
                    bigquery.SchemaField("guest_id",    "STRING"),
                    bigquery.SchemaField("displayName", "STRING"),
                    bigquery.SchemaField("email",       "STRING"),
                    bigquery.SchemaField("firstName",   "STRING"),
                    bigquery.SchemaField("lastName",    "STRING"),
                    bigquery.SchemaField("whereFound",  "STRING"),
                    bigquery.SchemaField("status",      "INTEGER"),
                    bigquery.SchemaField("newsletter",  "INTEGER"),
                ],
            ),
            "unlocks": self._upload(
                "unlocks",
                self._load_unlocks(),
                [
                    bigquery.SchemaField("time",     "TIMESTAMP"),
                    bigquery.SchemaField("location", "STRING"),
                    bigquery.SchemaField("barcode",  "STRING"),
                ],
            ),
            "certifications": self._upload(
                "certifications",
                self._load_certifications(),
                [
                    bigquery.SchemaField("user_id",      "STRING"),
                    bigquery.SchemaField("tool_id",      "INTEGER"),
                    bigquery.SchemaField("tool_name",    "STRING"),
                    bigquery.SchemaField("certifier_id", "STRING"),
                    bigquery.SchemaField("date",         "TIMESTAMP"),
                    bigquery.SchemaField("level",        "INTEGER"),
                ],
            ),
        }
        cherrypy.response.headers["Content-Type"] = "application/json"
        return json.dumps({"status": "ok", "rows_uploaded": results}).encode()
