import datetime


def timeAgo(days=0, hours=0):
    return datetime.datetime.now() - datetime.timedelta(days=days, hours=hours)


def testData():
    d = {
        "visits": [
            {
                "start": timeAgo(days=7, hours=1),
                "leave": timeAgo(days=7, hours=0),
                "barcode": "100091",
                "status": "Out"
            },
            {
                "start": timeAgo(days=7, hours=1),
                "leave": timeAgo(days=7, hours=0),
                "barcode": "100032",
                "status": "Out"
            },
            {
                "start": timeAgo(days=7, hours=2),
                "leave": timeAgo(days=7, hours=0.5),
                "barcode": "202107310001",
                "status": "Out"
            },
            {
                "start": timeAgo(hours=1),
                "barcode": "100091",
                "status": "In"
            },
            {
                "start": timeAgo(hours=1),
                "barcode": "202107310001",
                "status": "In"
            },
            {
                "start": timeAgo(hours=1),
                "barcode": "100032",
                "status": "In"
            },
        ],
        "members": [{
            "barcode": "100090",
            "displayName": "Daughter N",
            "firstName": "Daughter",
            "lastName": "Name",
            "email": "fake2@email.com",
            "membershipExpires": timeAgo(days=-30),
        }, {
            "barcode": "100091",
            "displayName": "Member N",
            "firstName": "Member",
            "lastName": "Name",
            "email": "fake@email.com",
            "membershipExpires": timeAgo(days=-30),
        }, {
            "barcode": "100032",
            "displayName": "Average J",
            "firstName": "Average",
            "lastName": "Joe",
            "email": "fake@email.com",
            "membershipExpires": timeAgo(days=-30)
        },
            {
            "barcode": "100093",
            "displayName": "Fred N",
            "firstName": "Fred",
            "lastName": "Name",
            "email": "fakeFreddie@email.com",
            "membershipExpires": timeAgo(days=-30),
        }],
        "accounts": [{
            "user": "admin",
            "password": "password",
            "barcode": "100091",
            "role": 0xFF
        },
            {
            "user": "joe",
            "password": "password",
            "barcode": "100032",
            "role": 0x40
        }],
        "teams": [{
            "team_id": 1,
            "program_name": "TFI",
            "program_number": 100,
            "team_name": "Crazy Contraptions",
            "start_date": datetime.datetime(year=2021, month=5, day=1),
            "active": 1,
            "members": [
                {"barcode": "100091", "type": 2},
                {"barcode": "100032", "type": 0}
            ]
        },
            {
            "team_id": 2,
            "program_name": "TFI",
            "program_number": 100,
            "team_name": "Crazy Contraptions",
            "start_date": datetime.datetime(year=2020, month=5, day=1),
            "active": 1,
            "members": [
                {"barcode": "100091", "type": 2},
                {"barcode": "100032", "type": 0}
            ]
        },
            {
            "team_id": 3,
            "program_name": "TFI",
            "program_number": 400,
            "team_name": "Inactive team",
            "start_date": datetime.datetime(year=2020, month=5, day=1),
            "active": 0,
            "members": [
                {"barcode": "100091", "type": 2},
                {"barcode": "100032", "type": 0}
            ]
        }

        ],
        "certifications": [
            # Member 100091 across many tools with increasing levels
            {"barcode": "100091", "tool_id": 1,  "level": 10, "date": timeAgo(days=60), "certifier": "LEGACY"},
            {"barcode": "100091", "tool_id": 2,  "level": 20, "date": timeAgo(days=50), "certifier": "LEGACY"},
            {"barcode": "100091", "tool_id": 3,  "level": 30, "date": timeAgo(days=40), "certifier": "LEGACY"},
            {"barcode": "100091", "tool_id": 4,  "level": 40, "date": timeAgo(days=30), "certifier": "LEGACY"},
            {"barcode": "100091", "tool_id": 5,  "level": 10, "date": timeAgo(days=25), "certifier": "100091"},
            {"barcode": "100091", "tool_id": 6,  "level": 20, "date": timeAgo(days=20), "certifier": "100091"},
            {"barcode": "100091", "tool_id": 7,  "level": 30, "date": timeAgo(days=15), "certifier": "100091"},
            {"barcode": "100091", "tool_id": 8,  "level": 40, "date": timeAgo(days=14), "certifier": "100091"},
            {"barcode": "100091", "tool_id": 9,  "level": 10, "date": timeAgo(days=13), "certifier": "100091"},
            {"barcode": "100091", "tool_id": 10, "level": 20, "date": timeAgo(days=12), "certifier": "100091"},
            {"barcode": "100091", "tool_id": 11, "level": 30, "date": timeAgo(days=11), "certifier": "100091"},
            {"barcode": "100091", "tool_id": 12, "level": 40, "date": timeAgo(days=10), "certifier": "100091"},
            {"barcode": "100091", "tool_id": 13, "level": 10, "date": timeAgo(days=9),  "certifier": "100091"},
            {"barcode": "100091", "tool_id": 14, "level": 20, "date": timeAgo(days=8),  "certifier": "100091"},
            {"barcode": "100091", "tool_id": 15, "level": 30, "date": timeAgo(days=7),  "certifier": "100091"},
            {"barcode": "100091", "tool_id": 16, "level": 40, "date": timeAgo(days=6),  "certifier": "100091"},
            {"barcode": "100091", "tool_id": 17, "level": 10, "date": timeAgo(days=5),  "certifier": "100091"},
            {"barcode": "100091", "tool_id": 18, "level": 20, "date": timeAgo(days=4),  "certifier": "100091"},
            {"barcode": "100091", "tool_id": 19, "level": 30, "date": timeAgo(days=3),  "certifier": "100091"},

            # Member 100032 with a mix including NONE to show absence, and CERTIFIED
            {"barcode": "100032", "tool_id": 1,  "level": 0,  "date": "",                 "certifier": "LEGACY"},
            {"barcode": "100032", "tool_id": 4,  "level": 10, "date": timeAgo(days=20),    "certifier": "100091"},
            {"barcode": "100032", "tool_id": 10, "level": 10, "date": timeAgo(days=18),    "certifier": "100091"},
            {"barcode": "100032", "tool_id": 15, "level": 20, "date": timeAgo(days=10),    "certifier": "100091"},
            {"barcode": "100032", "tool_id": 18, "level": 10, "date": timeAgo(days=2),     "certifier": "100091"}
            ,
            {"barcode": "100091", "tool_id": 1,  "level": 30, "date": timeAgo(days=2),  "certifier": "100091"},
            {"barcode": "100091", "tool_id": 2,  "level": 40, "date": timeAgo(days=2),  "certifier": "100091"},
            {"barcode": "100091", "tool_id": 3,  "level": 10, "date": timeAgo(days=1),  "certifier": "100091"},
            {"barcode": "100091", "tool_id": 4,  "level": 20, "date": timeAgo(days=1),  "certifier": "100091"},
            {"barcode": "100032", "tool_id": 5,  "level": 30, "date": timeAgo(days=12), "certifier": "100091"},
            {"barcode": "100032", "tool_id": 6,  "level": 20, "date": timeAgo(days=9),  "certifier": "100091"},
            {"barcode": "100032", "tool_id": 7,  "level": 30, "date": timeAgo(days=7),  "certifier": "100091"},
            {"barcode": "100032", "tool_id": 8,  "level": 40, "date": timeAgo(days=6),  "certifier": "100091"},
            {"barcode": "100090", "tool_id": 1,  "level": 10, "date": timeAgo(days=14), "certifier": "100091"},
            {"barcode": "100090", "tool_id": 4,  "level": 10, "date": timeAgo(days=13), "certifier": "100091"},
            {"barcode": "100090", "tool_id": 10, "level": 20, "date": timeAgo(days=11), "certifier": "100091"},
            {"barcode": "100090", "tool_id": 15, "level": 30, "date": timeAgo(days=10), "certifier": "100091"},
            {"barcode": "100090", "tool_id": 17, "level": 10, "date": timeAgo(days=5),  "certifier": "100091"},
            {"barcode": "100093", "tool_id": 3,  "level": 20, "date": timeAgo(days=16), "certifier": "100091"},
            {"barcode": "100093", "tool_id": 6,  "level": 30, "date": timeAgo(days=15), "certifier": "100091"},
            {"barcode": "100093", "tool_id": 9,  "level": 10, "date": timeAgo(days=12), "certifier": "100091"},
            {"barcode": "100093", "tool_id": 12, "level": 20, "date": timeAgo(days=11), "certifier": "100091"},
            {"barcode": "100093", "tool_id": 14, "level": 30, "date": timeAgo(days=8),  "certifier": "100091"},
            {"barcode": "100093", "tool_id": 18, "level": 10, "date": timeAgo(days=4),  "certifier": "100091"},
            {"barcode": "100093", "tool_id": 19, "level": 20, "date": timeAgo(days=3),  "certifier": "100091"}
        ],
        "customReports": [{
            "report_id": 1,
            "name": "fred",
            "sql_text": "SELECT * FROM members;"}
        ],
        "logEvents": [{
            "what": "Bulk Add",
            "barcode": "100091",
            "date": timeAgo(hours=1)
        }],
        "unlocks": [{
            "time": timeAgo(hours=1),
            "location": "TFI",
            "barcode": "100091"
        }],
        "guests": [{
            "guest_id": "202107310001",
            "displayName": "Random G.",
            "email": "spam@email.com",
            "firstName": "Random",
            "lastName": "Guest",
            "whereFound": "invited",
            "status": "1",
            "newsletter": 1
        }],
        "devices": [{
            "mac": "87:65:43:21",
            "name": "Phone",
            "barcode": "100091"
        }],
        "config": [{
            "key": "grace_period",
            "value": "15"
        }]
    }
    extra_members = []
    base_id = 200000
    first_names = [
        "Alex","Jordan","Taylor","Casey","Riley","Morgan","Avery","Quinn","Skyler","Reese",
        "Jamie","Cameron","Drew","Peyton","Rowan","Hayden","Emerson","Parker","Sage","Charlie"
    ]
    last_names = [
        "Smith","Johnson","Brown","Taylor","Anderson","Thomas","Jackson","White","Harris","Martin",
        "Thompson","Garcia","Martinez","Robinson","Clark","Rodriguez","Lewis","Lee","Walker","Hall"
    ]
    def gen_name(idx):
        fn = first_names[idx % len(first_names)]
        ln = last_names[(idx // len(first_names)) % len(last_names)]
        return fn, ln
    for i in range(1, 251):
        b = str(base_id + i)
        fn, ln = gen_name(i)
        extra_members.append({
            "barcode": b,
            "displayName": f"{fn} {ln}",
            "firstName": fn,
            "lastName": ln,
            "email": f"{fn.lower()}.{ln.lower()}@email.com",
            "membershipExpires": timeAgo(days=-30),
        })
    for i in range(251, 271):
        b = str(base_id + i)
        fn, ln = gen_name(i)
        extra_members.append({
            "barcode": b,
            "displayName": f"{fn} {ln}",
            "firstName": fn,
            "lastName": ln,
            "email": f"{fn.lower()}.{ln.lower()}@email.com",
            "membershipExpires": timeAgo(days=-30),
        })
    d["members"].extend(extra_members)
    for m in d["members"]:
        dn = str(m.get("displayName", ""))
        if dn.startswith("Member ") or dn.startswith("Member"):
            fn, ln = gen_name(int(m["barcode"]) % 1000)
            m["firstName"], m["lastName"] = fn, ln
            m["displayName"] = f"{fn} {ln}"
            m["email"] = f"{fn.lower()}.{ln.lower()}@email.com"
    levels = [10, 20, 30, 40]
    tool_ids = list(range(1, 20))
    extra_certs = []
    count = 0
    for idx, m in enumerate(extra_members):
        for j in range(2):
            if count >= 50:
                break
            t = tool_ids[(idx + j) % len(tool_ids)]
            lvl = levels[(idx + j) % len(levels)]
            extra_certs.append({
                "barcode": m["barcode"],
                "tool_id": t,
                "level": lvl,
                "date": timeAgo(days=idx % 30 + 1),
                "certifier": "100091"
            })
            count += 1
        if count >= 50:
            break
    d["certifications"].extend(extra_certs)
    # Add 5 more Basic (Red Dot) certifications for 3D printers (tool_id 4)
    extra_basic = []
    for i, m in enumerate(extra_members[:5], start=1):
        extra_basic.append({
            "barcode": m["barcode"],
            "tool_id": 4,
            "level": 1,  # Basic (Red Dot)
            "date": timeAgo(days=i),
            "certifier": "100091"
        })
    d["certifications"].extend(extra_basic)
    extra_visits = []
    now_start = timeAgo(hours=1)
    # Ensure a couple of baseline members are checked in as well
    extra_visits.append({
        "start": now_start,
        "barcode": "100091",
        "status": "In"
    })
    extra_visits.append({
        "start": now_start,
        "barcode": "100032",
        "status": "In"
    })
    for m in extra_members[:50]:
        extra_visits.append({
            "start": now_start,
            "barcode": m["barcode"],
            "status": "In"
        })
    d["visits"].extend(extra_visits)
    return d
