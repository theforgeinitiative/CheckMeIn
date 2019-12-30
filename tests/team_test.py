
from unittest.mock import patch

import cherrypy
from cherrypy.test import helper
from cherrypy.lib.sessions import RamSession

from checkMeIn import CheckMeIn


class SimpleCPTest(helper.CPWebCase):
    @staticmethod
    def setup_server():
        cherrypy.tree.mount(CheckMeIn(), '/', {})

    def test_create(self):
        self.getPage("/createTeam?team_name=Test")
        self.assertStatus('200 OK')

    def test_add(self):
        self.getPage(
            "/addTeamMembers?team_id=1&students=100090&mentors=100091&coaches=100092")
        self.assertStatus('200 OK')

    def test_attendance(self):
        self.getPage(
            "/teamAttendance?team_id=1&date=12-01-19&startTime=11:30&endTime=12:30")
        self.assertStatus('200 OK')
