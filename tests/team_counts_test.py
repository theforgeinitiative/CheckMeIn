"""Tests for checked-in counts grouped by member type.

Three layers:
  * plain unit tests on TeamMember objects (no database)
  * tests against a private, temporary database built by the real Engine
  * web tests that insert their own uniquely named rows into the shared test
    database, check the rendered pages, and remove the rows afterwards
"""
import datetime
import re
import sqlite3

import pytest

import CPtest
from engine import Engine
from teams import TeamMember, TeamMemberType, Teams

LABELS = ["Students", "Coaches", "Mentors", "Other"]


def member(name, memberType, present=False):
    return TeamMember(name, name.lower(), memberType, present)


class TestGroupMembersByType:
    def test_groups_are_in_display_order_even_when_empty(self):
        groups = Teams().groupMembersByType([])
        assert [label for label, _, _ in groups] == LABELS
        assert all(members == [] and numPresent == 0
                   for _, members, numPresent in groups)

    def test_members_land_in_their_own_group_and_keep_order(self):
        students = [member("a", TeamMemberType.student),
                    member("b", TeamMemberType.student)]
        coach = member("c", TeamMemberType.coach)
        mentor = member("m", TeamMemberType.mentor)
        other = member("o", TeamMemberType.other)
        groups = dict((label, members) for label, members, _ in
                      Teams().groupMembersByType(
                          [students[0], coach, mentor, other, students[1]]))
        assert groups["Students"] == students
        assert groups["Coaches"] == [coach]
        assert groups["Mentors"] == [mentor]
        assert groups["Other"] == [other]

    def test_count_is_only_members_who_are_present(self):
        members = [member("a", TeamMemberType.student, True),
                   member("b", TeamMemberType.student, False),
                   member("c", TeamMemberType.student, True),
                   member("d", TeamMemberType.coach, False),
                   member("e", TeamMemberType.other, True)]
        counts = dict((label, numPresent) for label, _, numPresent in
                      Teams().groupMembersByType(members))
        assert counts == {"Students": 2, "Coaches": 0,
                          "Mentors": 0, "Other": 1}

    def test_types_read_from_the_database_are_plain_ints(self):
        # sqlite hands back plain ints, not TeamMemberType values
        members = [TeamMember("s", "1", 0, True), TeamMember("c", "2", 2, True),
                   TeamMember("m", "3", 1, False), TeamMember("o", "4", -1, True)]
        counts = dict((label, numPresent) for label, _, numPresent in
                      Teams().groupMembersByType(members))
        assert counts == {"Students": 1, "Coaches": 1,
                          "Mentors": 0, "Other": 1}


class TestGetMemberCounts:
    def test_counts_by_type_and_total(self):
        members = [member("a", TeamMemberType.student, True),
                   member("b", TeamMemberType.student, True),
                   member("c", TeamMemberType.coach, True),
                   member("d", TeamMemberType.mentor, False),
                   member("e", TeamMemberType.other, True)]
        counts, total = Teams().getMemberCounts(members)
        assert total == 4
        assert counts == {TeamMemberType.student: 2, TeamMemberType.coach: 1,
                          TeamMemberType.mentor: 0, TeamMemberType.other: 1}

    def test_nobody_present(self):
        counts, total = Teams().getMemberCounts(
            [member("a", TeamMemberType.student, False)])
        assert total == 0
        assert set(counts.values()) == {0}

    def test_no_members(self):
        counts, total = Teams().getMemberCounts([])
        assert total == 0
        assert len(counts) == 4

    def test_int_typed_members_are_counted(self):
        counts, total = Teams().getMemberCounts(
            [TeamMember("x", "1", 2, True)])
        assert total == 1
        assert counts[TeamMemberType.coach] == 1


# ---- private database built by the real Engine -----------------------------

NOW = datetime.datetime(2026, 1, 1, 12, 0, 0)


@pytest.fixture
def conn(tmp_path):
    engine = Engine(str(tmp_path) + "/", "unit.db", True)
    connection = engine.dbConnect()
    yield connection
    connection.close()


def add_team(conn, number=1):
    return conn.execute(
        '''INSERT INTO teams(program_name, program_number, team_name,
                             start_date, active)
           VALUES ('TST', ?, 'Test Team', ?, 1)''', (number, NOW)).lastrowid


def add_member(conn, teamId, barcode, name, memberType):
    conn.execute(
        '''INSERT INTO members(barcode, displayName, firstName, lastName,
                               email, membershipExpires)
           VALUES (?, ?, '', '', '', ?)''', (barcode, name, NOW))
    conn.execute("INSERT INTO team_members VALUES (?, ?, ?)",
                 (teamId, barcode, int(memberType)))


def add_visit(conn, barcode, status, minutesAfterNoon):
    start = NOW + datetime.timedelta(minutes=minutesAfterNoon)
    conn.execute(
        "INSERT INTO visits(start, leave, barcode, status) VALUES (?,?,?,?)",
        (start, None if status == "In" else start, barcode, status))


class TestGetTeamMembers:
    def test_sorted_by_type_then_name_ignoring_case(self, conn):
        team = add_team(conn)
        # inserted in scrambled order on purpose
        add_member(conn, team, "1", "Otto", TeamMemberType.other)
        add_member(conn, team, "2", "zed", TeamMemberType.student)
        add_member(conn, team, "3", "mia", TeamMemberType.mentor)
        add_member(conn, team, "4", "Bob", TeamMemberType.student)
        add_member(conn, team, "5", "Carl", TeamMemberType.coach)
        add_member(conn, team, "6", "alice", TeamMemberType.student)
        names = [m.name for m in Teams().getTeamMembers(conn, team)]
        assert names == ["alice", "Bob", "zed", "Carl", "mia", "Otto"]

    def test_present_follows_the_latest_visit(self, conn):
        team = add_team(conn)
        for barcode in "abcde":
            add_member(conn, team, barcode, "member " + barcode,
                       TeamMemberType.student)
        # a: never visited
        add_visit(conn, "b", "In", 10)                            # in
        add_visit(conn, "c", "In", 10)                            # in, then out
        add_visit(conn, "c", "Out", 20)
        add_visit(conn, "d", "Out", 10)                           # out, then in
        add_visit(conn, "d", "In", 20)
        add_visit(conn, "e", "Forgot", 10)                        # left w/o checkout
        present = dict((m.barcode, m.present)
                       for m in Teams().getTeamMembers(conn, team))
        assert present == {"a": False, "b": True, "c": False,
                           "d": True, "e": False}

    def test_only_members_of_the_requested_team(self, conn):
        team1, team2 = add_team(conn, 1), add_team(conn, 2)
        add_member(conn, team1, "1", "On One", TeamMemberType.student)
        add_member(conn, team2, "2", "On Two", TeamMemberType.student)
        assert [m.name for m in Teams().getTeamMembers(conn, team1)] == ["On One"]

    def test_database_to_grouped_counts(self, conn):
        team = add_team(conn)
        add_member(conn, team, "1", "S1", TeamMemberType.student)
        add_member(conn, team, "2", "S2", TeamMemberType.student)
        add_member(conn, team, "3", "C1", TeamMemberType.coach)
        add_member(conn, team, "4", "M1", TeamMemberType.mentor)
        add_member(conn, team, "5", "O1", TeamMemberType.other)
        for barcode in ("1", "3", "5"):
            add_visit(conn, barcode, "In", 10)
        teams = Teams()
        groups = teams.groupMembersByType(teams.getTeamMembers(conn, team))
        assert [(label, [m.name for m in members], numPresent)
                for label, members, numPresent in groups] == [
            ("Students", ["S1", "S2"], 1), ("Coaches", ["C1"], 1),
            ("Mentors", ["M1"], 0), ("Other", ["O1"], 1)]


# ---- pages, using the shared test database --------------------------------

TEST_DB = "testData/test.db"
BARCODES = ["990001", "990002", "990003", "990004", "990005", "990006"]


def squash(html):
    return re.sub(r"\s+", " ", html)


def section(html, label):
    """The part of the team page belonging to one category heading."""
    found = re.search(r"<H3>%s:.*?(?=<H3>|</fieldset>)" % label, html,
                      re.DOTALL)
    assert found, "no section headed %s" % label
    return found.group(0)


class TeamCountsWebTest(CPtest.CPTest):
    """Team 'ZZT9901' with: Students amy student (out), Sam Student (in);
    Coach Cara Coach (in); Mentor Molly Mentor (out);
    Others Olive Other (in), Otis Other (out)."""

    def setUp(self):
        db = sqlite3.connect(TEST_DB)
        self.teamId = db.execute(
            '''INSERT INTO teams(program_name, program_number, team_name,
                                 start_date, active)
               VALUES ('ZZT', 9901, 'Count Test', ?, 1)''',
            (datetime.datetime.now(),)).lastrowid
        people = [("990001", "Sam Student", TeamMemberType.student, True),
                  ("990002", "amy student", TeamMemberType.student, False),
                  ("990003", "Cara Coach", TeamMemberType.coach, True),
                  ("990004", "Molly Mentor", TeamMemberType.mentor, False),
                  ("990005", "Olive Other", TeamMemberType.other, True),
                  ("990006", "Otis Other", TeamMemberType.other, False)]
        now = datetime.datetime.now()
        for barcode, name, memberType, isIn in people:
            db.execute(
                '''INSERT INTO members(barcode, displayName, firstName,
                       lastName, email, membershipExpires)
                   VALUES (?, ?, '', '', '', ?)''',
                (barcode, name, now + datetime.timedelta(days=30)))
            db.execute("INSERT INTO team_members VALUES (?, ?, ?)",
                       (self.teamId, barcode, int(memberType)))
            if isIn:
                db.execute(
                    "INSERT INTO visits(start, leave, barcode, status) "
                    "VALUES (?, ?, ?, 'In')", (now, now, barcode))
        db.commit()
        db.close()
        self.addCleanup(self.removeTestData)

    def removeTestData(self):
        db = sqlite3.connect(TEST_DB)
        marks = ",".join("?" * len(BARCODES))
        db.execute("DELETE FROM visits WHERE barcode IN (%s)" % marks, BARCODES)
        db.execute("DELETE FROM team_members WHERE team_id = ?", (self.teamId,))
        db.execute("DELETE FROM members WHERE barcode IN (%s)" % marks, BARCODES)
        db.execute("DELETE FROM teams WHERE team_id = ?", (self.teamId,))
        db.commit()
        db.close()

    def teamPage(self):
        with self.patch_session():
            self.getPage("/teams/?team_id=%d" % self.teamId)
        self.assertStatus('200 OK')
        return self.body.decode()

    # -- team page

    def test_team_page_sections_in_order_with_counts(self):
        html = self.teamPage()
        headings = ["Students: 1 in building", "Coaches: 1 in building",
                    "Mentors: 0 in building", "Other: 1 in building"]
        positions = [html.index(h) for h in headings]
        assert positions == sorted(positions)

    def test_team_page_members_sit_in_their_own_section(self):
        html = self.teamPage()
        expected = {"Students": ["amy student", "Sam Student"],
                    "Coaches": ["Cara Coach"],
                    "Mentors": ["Molly Mentor"],
                    "Other": ["Olive Other", "Otis Other"]}
        everyone = [n for names in expected.values() for n in names]
        for label, names in expected.items():
            text = section(html, label)
            for name in everyone:
                assert (name in text) == (name in names), (label, name)

    def test_team_page_alphabetical_within_section(self):
        html = self.teamPage()
        students = section(html, "Students")
        assert students.index("amy student") < students.index("Sam Student")

    def test_team_page_keeps_in_out_controls(self):
        html = self.teamPage()
        for barcode in BARCODES:
            # one In and one Out radio (the New Season form reuses the name
            # for a checkbox, so count radios only)
            assert html.count('type="radio" name="%s"' % barcode) == 2, barcode
        checked = {"990001": "in", "990002": "out", "990003": "in",
                   "990004": "out", "990005": "in", "990006": "out"}
        for barcode, value in checked.items():
            assert re.search(r'name="%s"\s+checked="checked"\s+value="%s"'
                             % (barcode, value), html), (barcode, value)
        assert 'name="team_id" value="%d"' % self.teamId in html
        assert 'value="Update"' in html

    def test_update_checks_people_in_and_out(self):
        with self.patch_session():
            self.getPage("/teams/update?team_id=%d&990002=in&990001=out"
                         % self.teamId)
        self.assertStatus('303 See Other')
        html = self.teamPage()
        assert "Students: 1 in building" in html
        assert re.search(r'name="990002"\s+checked="checked"\s+value="in"', html)
        assert re.search(r'name="990001"\s+checked="checked"\s+value="out"', html)

    # -- team report

    def reportBlock(self):
        with self.patch_session():
            self.getPage("/reports/teamList")
        self.assertStatus('200 OK')
        found = re.search(r"ZZT9901 - Count Test(.*?)</UL></LI>",
                          self.body.decode(), re.DOTALL)
        assert found, "test team missing from report"
        return squash(found.group(1))

    def test_report_shows_total_and_per_type_counts(self):
        block = self.reportBlock()
        assert "Checked in: 3" in block
        assert "(Student: 1, Coach: 1, Mentor: 0, Other: 1)" in block

    def test_report_lists_other_members(self):
        block = self.reportBlock()
        assert "Olive Other (Other)" in block
        assert "Otis Other (Other)" in block

    def test_report_roster_order(self):
        block = self.reportBlock()
        order = ["amy student", "Sam Student", "Cara Coach (Coach)",
                 "Molly Mentor (Mentor)", "Olive Other (Other)"]
        positions = [block.index(name) for name in order]
        assert positions == sorted(positions)
