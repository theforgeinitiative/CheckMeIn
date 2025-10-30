import cherrypy
from webBase import WebBase
import os
import json


class WebCertifications(WebBase):
    # Certifications
    def showCertifications(self, message, tools, certifications, show_table_header=True, show_left_names=True, show_right_names=True):
        return self.template('certifications.mako',
                             message=message,
                             tools=tools,
                             show_table_header=show_table_header,
                             show_left_names=show_left_names,
                             show_right_names=show_right_names,
                             certifications=certifications)

    @cherrypy.expose
    def certify(self, all=False):
        certifier_id = self.getBarcode("/certifications/certify")
        message = ''
        with self.dbConnect() as dbConnection:
            members = self.engine.members.getActive(
                dbConnection) if all else self.engine.visits.getMembersInBuilding(dbConnection)

            return self.template('certify.mako', message=message,
                                 certifier=self.engine.members.getName(dbConnection,
                                                                       certifier_id)[1],
                                 certifier_id=certifier_id,
                                 members_in_building=members,
                                 tools=self.engine.certifications.getListCertifyTools(dbConnection, certifier_id))

    @cherrypy.expose
    def addCertification(self, member_id, tool_id, level):
        certifier_id = self.getBarcode("/certifications/certify")
        # We don't check here for valid tool since someone is forging HTML to put an invalid one
        # and we'll catch it with the email out...\
        with self.dbConnect() as dbConnection:
            self.engine.certifications.addNewCertification(dbConnection,
                                                           member_id, tool_id, level, certifier_id)
        with self.dbConnect() as dbConnection:  # separate out committing from getting
            memberName = self.engine.members.getName(
                dbConnection, member_id)[1]
            certifierName = self.engine.members.getName(
                dbConnection, certifier_id)[1]
            level = self.engine.certifications.getLevelName(level)
            tool = self.engine.certifications.getToolName(
                dbConnection, tool_id)

            self.engine.certifications.emailCertifiers(
                memberName, tool, level, certifierName)

        return self.template('congrats.mako', message='',
                             certifier_id=certifier_id,
                             memberName=memberName,
                             level=level,
                             tool=tool)

    @cherrypy.expose
    def index(self):
        message = ''
        with self.dbConnect() as dbConnection:
            tools = self.engine.certifications.getAllTools(dbConnection)
            certifications = self.engine.certifications.getInBuildingUserList(
                dbConnection)

            return self.showCertifications(message, tools, certifications)

    @cherrypy.expose
    def team(self, team_id):
        message = ''
        with self.dbConnect() as dbConnection:
            message = 'Certifications for team: ' + \
                self.engine.teams.teamNameFromId(dbConnection, team_id)
            tools = self.engine.certifications.getAllTools(dbConnection)
            certifications = self.engine.certifications.getTeamUserList(
                dbConnection, team_id)

            return self.showCertifications(message, tools, certifications)

    @cherrypy.expose
    def user(self, barcode):
        message = ''
        with self.dbConnect() as dbConnection:
            message = 'Certifications for Individual'
            tools = self.engine.certifications.getAllTools(dbConnection)
            certifications = self.engine.certifications.getUserList(
                dbConnection, user_id=barcode)

            return self.showCertifications(message, tools, certifications)

    def getBoolean(self, term):
        if term == '0' or term.upper() == 'FALSE':
            return False
        return True

    @cherrypy.expose
    def monitor(self, tools, start_row=0, show_left_names="True", show_right_names="True", show_table_header="True"):
        message = ''
        with self.dbConnect() as dbConnection:
            certifications = self.engine.certifications.getInBuildingUserList(
                dbConnection)
            start = int(start_row)
            if start <= len(certifications):
                # This depends on python 3.6 or higher for the dictionary to be ordered by insertion order
                listCertKeys = list(certifications.keys())[start:]
                subsetCerts = {}
                for cert in listCertKeys:
                    subsetCerts[cert] = certifications[cert]
                certifications = subsetCerts
            else:
                return self.template("blank.mako")

            show_table_header = self.getBoolean(show_table_header)
            show_left_names = self.getBoolean(show_left_names)
            show_right_names = self.getBoolean(show_right_names)

            tools = self.engine.certifications.getToolsFromList(
                dbConnection, tools)

            return self.showCertifications(message, tools, certifications, show_table_header, show_left_names, show_right_names)

    @cherrypy.expose
    def all(self):
        message = ''
        with self.dbConnect() as dbConnection:
            tools = self.engine.certifications.getAllTools(dbConnection)
            certifications = self.engine.certifications.getAllUserList(
                dbConnection)

            return self.showCertifications(message, tools, certifications)

    @cherrypy.expose
    def v2(self, debug=None):
        with self.dbConnect() as dbConnection:
            tools = self.engine.certifications.getAllTools(dbConnection)
            users = self.engine.certifications.getAllUserList(dbConnection)
        # Load curated images mapping if available
        images_map = {}
        try:
            static_root = os.path.join(os.getcwd(), 'static', 'tools')
            with open(os.path.join(static_root, 'images.json'), 'r', encoding='utf-8') as f:
                images_map = json.load(f)
        except Exception:
            images_map = {}
        tool_map = {}
        for t in tools:
            tool_id = t[0]
            tool_name = t[1]
            # Resolve curated image: by id first, then by lowercased name
            curated_url = (
                images_map.get(str(tool_id))
                or images_map.get(tool_name)
                or images_map.get(tool_name.lower())
                or images_map.get(tool_name.replace(' ', '_').lower())
            )
            base_static = f"/static/tools/{tool_id}"
            tool_map[t[0]] = {
                'id': t[0],
                'name': tool_name,
                'group': t[2],
                'members': [],
                'image_url': curated_url or f"{base_static}.avif",
                'img_avif': f"{base_static}.avif",
                'img_png': f"{base_static}.png",
                'img_jpg': f"{base_static}.jpg"
            }
        for user_id, tooluser in users.items():
            for tid, tl in tooluser.tools.items():
                level = int(tl[1]) if tl and tl[1] is not None else 0
                if level > 0:
                    base_label = self.engine.certifications.getLevelName(level)
                    # Customize labels per request
                    if level == 1:
                        label = 'Basic (Red Dot)'
                    elif level == 10:
                        label = 'Certified (Green Dot)'
                    else:
                        label = base_label
                    tool_map.get(tid, {}).get('members', []).append({
                        'displayName': tooluser.displayName,
                        'barcode': tooluser.barcode,
                        'level': level,
                        'level_name': label
                    })
        for v in tool_map.values():
            v['members'] = sorted(v['members'], key=lambda m: (m['level'], m['displayName']))
        tools_data = [tool_map[t[0]] for t in tools]
        levels = [
            {'value': 10, 'name': self.engine.certifications.getLevelName(10), 'class': 'level-10'},
            {'value': 20, 'name': self.engine.certifications.getLevelName(20), 'class': 'level-20'},
            {'value': 30, 'name': self.engine.certifications.getLevelName(30), 'class': 'level-30'},
            {'value': 40, 'name': self.engine.certifications.getLevelName(40), 'class': 'level-40'},
        ]
        if debug:
            cherrypy.response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return json.dumps(tools_data).encode('utf-8')
        return self.template('certifications_v2.mako', tools=tools_data, levels=levels, tools_json=json.dumps(tools_data))
