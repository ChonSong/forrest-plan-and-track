"""
OneTag HMAS — Database Seed Script (Schema-Aware with FK Support)
Dynamically discovers column names via PRAGMA and seeds accordingly.
Captures IDs from reference tables for use in FK columns.
"""

import sqlite3, os, uuid, random
from datetime import datetime, timedelta, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'onetag.db')

def uid():
    return str(uuid.uuid4()).upper()

def d(days=0, hours=0):
    return (datetime.now(timezone.utc) - timedelta(days=days, hours=hours)).isoformat()

random.seed(42)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Ensure schema exists
cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
if cur.fetchone()[0] == 0:
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prisma', 'schema.sqlite.sql')) as f:
        conn.executescript(f.read())
    conn.commit()
    print("  ✅ Schema created (103 tables)")

_cache = {}
_null_cache = {}

def table_columns(table):
    if table not in _cache:
        cur.execute(f'PRAGMA table_info("{table}")')
        _cache[table] = {row[1] for row in cur.fetchall()}
    return _cache[table]

def not_null_cols(table):
    """Return dict of NOT NULL column names to their types, excluding PKs and auto-filled cols."""
    if table not in _null_cache:
        cur.execute(f'PRAGMA table_info("{table}")')
        result = {}
        for row in cur.fetchall():
            name, typ, not_null, is_pk = row[1], row[2], row[3], row[5]
            if not_null and not is_pk and name not in ('Id', 'CreatedDate', 'CreatedBy', 'ModifiedBy', 'DeletedBy', 'ModifiedDate', 'DeletedDate'):
                result[name] = typ
        _null_cache[table] = result
    return _null_cache[table]

def smart_insert(table, **values):
    cols = table_columns(table)
    
    vals = dict(values)
    
    # Auto-fill Id
    if 'Id' not in vals and 'Id' in cols:
        vals['Id'] = uid()
    
    # Auto-fill CreatedDate
    if 'CreatedDate' not in vals and 'CreatedDate' in cols:
        vals['CreatedDate'] = d(days=random.randint(1, 365))
    
    # Auto-fill CreatedBy, ModifiedBy, DeletedBy if they exist
    for ac in ['CreatedBy', 'ModifiedBy', 'DeletedBy']:
        if ac in cols and ac not in vals:
            vals[ac] = uid()
    
    # Auto-fill all remaining NOT NULL columns with type-appropriate defaults
    for nn_col, nn_type in not_null_cols(table).items():
        if nn_col not in vals:
            if nn_type == 'INTEGER':
                vals[nn_col] = 0
            elif nn_type == 'REAL':
                vals[nn_col] = 0.0
            elif nn_type == 'BLOB':
                vals[nn_col] = b''
            else:  # TEXT and everything else
                vals[nn_col] = ''
    
    # Filter to only existing columns
    valid = {k: v for k, v in vals.items() if k in cols}
    
    if not valid:
        return None
    
    col_names = list(valid.keys())
    quoted = [f'"{c}"' for c in col_names]
    placeholders = ', '.join(['?' for _ in col_names])
    stmt = f'INSERT OR IGNORE INTO "{table}" ({", ".join(quoted)}) VALUES ({placeholders})'
    try:
        cur.execute(stmt, list(valid.values()))
        return vals.get('Id')
    except Exception as e:
        print(f"  ⚠️  {table}: {e}")
        return None

print("🌱 Seeding OneTag HMAS database...")

# ── REFERENCE TABLES (capture all IDs) ─────────────────────────────────

# GroupTypes
gt = {name: smart_insert('GroupTypes', Id=uid(), Name=name, Description=desc)
      for name, desc in [('Vessel','Marine vessel'),('Platform','Fixed platform'),
                         ('Facility','Onshore facility'),('Division','Organisational division')]}

# SystemTypes
st = {k: smart_insert('SystemTypes', Id=uid(), Name=v, Description=d, Colour=c)
      for k, (v, d, c) in {'elec': ('Electrical','Power systems','#e74c3c'),
                           'mech': ('Mechanical','Equipment','#3498db'),
                           'hvac': ('HVAC','Heating/cooling','#2ecc71'),
                           'fire': ('Fire & Gas','Detection','#f39c12')}.items()}

# SystemCategories
sc = {name: smart_insert('SystemCategories', Id=uid(), Name=name, Description=desc)
      for name, desc in [('Critical','Safety-critical'),('Essential','Operationally essential'),
                         ('Standard','Standard system'),('Ancillary','Supporting system')]}

# AreaTypes
at = {name: smart_insert('AreaTypes', Id=uid(), Name=name, Description=desc, SecureArea=s, HighRisk=h)
      for name, desc, s, h in [('Production','Production zone',0,1),('Storage','Material storage',0,0),
                               ('Workshop','Workshop',0,0),('Control Room','Control room',1,0),
                               ('High Risk','High hazard',0,1)]}

# Departments
depts = {name: smart_insert('Departments', Id=uid(), Name=name, Description=desc)
         for name, desc in [('Operations','Ops'),('Maintenance','Maint'),('Safety','HSE'),
                            ('Engineering','Eng'),('Projects','Proj')]}

# UserRoles
urs = {name: smart_insert('UserRoles', Id=uid(), Name=name, RoleLevel=level, ReadOnly=0)
       for name, level in [('Operator',1),('Supervisor',2),('Manager',3),
                           ('Safety Officer',4),('Administrator',5)]}

# IsolationPointTypes
ipts = {name: smart_insert('IsolationPointTypes', Id=uid(), Name=name, Description=desc)
        for name, desc in [('Electrical Breaker','Electrical'),('Valve','Process valve'),
                           ('Blind/Blank','Pipe flange'),('Lockable Tag','Tagout'),
                           ('Physical Barrier','Barrier')]}

# WorkPermitTypes
wpts = {name: smart_insert('WorkPermitTypes', Id=uid(), Name=name, Prefix=prefix)
        for name, prefix in [('Hot Work','HOT'),('Cold Work','CLD'),('Confined Space','CSP'),
                             ('Working at Height','WAH'),('Electrical Isolation','ELI')]}

# ReasonCodes
rcs = {name: smart_insert('ReasonCodes', Id=uid(), Code=code, Name=name, Internal=0)
       for code, name in [('S01','Routine Maintenance'),('S02','Emergency Repair'),
                          ('S03','Planned Shutdown'),('S04','Testing'),('S05','Modification')]}

# LockoutDeviceTypes
ldts = [smart_insert('LockoutDeviceTypes', Id=uid(), Name=n, Colour=random.choice(['Red','Yellow']),
                     TotalCount=random.randint(10,50), TotalInUse=random.randint(1,20))
        for n in ['Padlock','Chain Lock','Valve Lockout','Breaker Lockout','Group Lock Box']]

# Permissions
perms = [smart_insert('Permissions', Id=uid(), Key=k, Name=n, Description=d, IsActive=1, SortOrder=0)
         for k,n,d in [('create_rfi','Create RFI','Create new'),('approve_iso','Approve Isolation','Approve'),
                       ('view_audit','View Audit','View'),('manage_users','Manage Users','Manage'),
                       ('close_permit','Close Permit','Close')]]

print("  ✅ Reference tables seeded")

# ── HIERARCHY ──────────────────────────────────────────────────────────

# Groups
gids = {name: smart_insert('Groups', Id=uid(), Name=name, Description=f'{name} group',
                            Code=f'GRP-{random.randint(100,999)}')
        for name in ['Alpha Platform','Bravo Platform','Delta Facility','Processing Plant','Storage Terminal']}

# Systems (need SystemTypeId, SystemCategoryId)
sys_ids = {}
for name, st_key, sc_key in [('Main Power Distribution','elec','Critical'),
                              ('Emergency Generator','elec','Critical'),
                              ('HVAC System A','hvac','Essential'),
                              ('Fire Water System','fire','Critical'),
                              ('Compressed Air','mech','Standard'),
                              ('Lighting System','elec','Ancillary'),
                              ('Gas Detection','fire','Critical')]:
    sid = uid()
    sys_ids[name] = sid
    smart_insert('Systems', Id=sid, Name=name, Description=f'{name} system',
                 Code=f'SYS-{name[:3].upper()}',
                 SystemTypeId=st.get(st_key), SystemCategoryId=sc.get(sc_key))
    # Capture a single system for later use
    SYSTEM_ID = sid

# Areas (need AreaTypeId, DepartmentId)
area_ids = {}
area_names = ['Production Deck A','Production Deck B','MCC Room','Control Room East',
              'Workshop North','Chemical Storage','Generator Room','SWBD Room']
for name in area_names:
    aid = uid()
    area_ids[name] = aid
    smart_insert('Areas', Id=aid, Name=name, Description=f'{name} area',
                 Code=f'AREA-{random.randint(100,999)}',
                 AreaTypeId=random.choice(list(at.values())),
                 DepartmentId=random.choice(list(depts.values())))

# Equipment
equip_ids = {}
for name in ['Motor Pump P-101','Motor Pump P-102','Compressor C-201','Fan F-301',
             'Transformer T-101','Switchboard SW-01','UPS Unit U-001','Generator G-001']:
    eid = uid()
    equip_ids[name] = eid
    smart_insert('Equipment', Id=eid, Name=name, SerialNumber=f'SN-{random.randint(10000,99999)}',
                 Description=name, AreaId=random.choice(list(area_ids.values())),
                 SystemId=random.choice(list(sys_ids.values())))

# IsolationPoints
ip_ids = []
for name in ['Breaker MCC-01','Breaker MCC-02','Valve PV-101','Valve PV-102',
             'Blind FL-201','Lockable Tag LT-01','Chain Lock CL-01',
             'Breaker SWBD-01','Valve XV-301','Blind FL-202']:
    ipid = uid()
    ip_ids.append(ipid)
    smart_insert('IsolationPoints', Id=ipid, Name=name, Description=f'{name} isolation',
                 IsolationPointTypeId=random.choice(list(ipts.values())),
                 AreaId=random.choice(list(area_ids.values())))
    # Link to random equipment
    smart_insert('EquipmentIsolations', Id=uid(),
                 EquipmentId=random.choice(list(equip_ids.values())),
                 IsolationPointId=ipid, Notes='', Secondary=0)

print("  ✅ Hierarchy seeded")

# ── COMPANIES ──────────────────────────────────────────────────────────

comp_ids = {}
for name in ['Pacific Maintenance','Delta Engineering','SafeWork Solutions',
             'Industrial Support','Oceania Fabrication']:
    cid = uid()
    comp_ids[name] = cid
    smart_insert('Companies', Id=cid, Name=name,
                 Phone=f'02-{random.randint(9000,9999)}',
                 Email=f'contact@{name.lower().replace(" ","")}.com',
                 Code=f'C-{random.randint(100,999)}')

print("  ✅ Companies seeded")

# ── USERS ──────────────────────────────────────────────────────────────

user_ids = {}
user_data = [('Sarah','Connor','sconnor','Operator'),('Mike','Chen','mchen','Operator'),
             ('Emma','Williams','ewilliams','Supervisor'),('James','Rodriguez','jrodriguez','Supervisor'),
             ('Lisa','Park','lpark','Manager'),('Tom','Baker','tbaker','Safety Officer'),
             ('Rachel','Green','rgreen','Safety Officer'),('David','Kim','dkim','Operator'),
             ('Nina','Patel','npatel','Operator'),('Oscar','Torres','otorres','Administrator'),
             ('Fiona','Black','fblack','Manager'),('George','Liu','gliu','Supervisor')]
for first, last, uname, role in user_data:
    uid_str = uid()
    user_ids[f'{first} {last}'] = uid_str
    smart_insert('Users', Id=uid_str, FirstName=first, LastName=last, UserName=uname,
                 Mobile=f'04{random.randint(10000000,99999999)}',
                 Email=f'{uname}@onetag.com.au', Position=role,
                 AccountLocked=0, BadgeSerialNumber=f'BADGE-{random.randint(1000,9999)}',
                 DepartmentId=random.choice(list(depts.values())),
                 CompanyId=random.choice(list(comp_ids.values())),
                 UserRoleId=urs.get(role))
    smart_insert('UserLogins', Id=uid_str, LastLogin=d(days=random.randint(0,30)),
                 LastPasswordChange=d(days=random.randint(30,180)),
                 PasswordSalt=b'salt', PasswordHash=b'hash', UserLoginStates=0)

print(f"  ✅ {len(user_ids)} users seeded")

# ── RFIS ───────────────────────────────────────────────────────────────

rfi_ids = []
for i in range(50):
    rid = uid()
    rfi_ids.append(rid)
    smart_insert('RFIs', Id=rid,
                 Description=f'{random.choice(["Isolate","Repair","Inspect","Replace"])} {random.choice(["pump","valve","motor","compressor","pipe"])} #{i+1}',
                 RFINumber=f'RFI-{2025000+i:04d}',
                 RFIState=random.choice([2,3,4,5,6,7,8,9,10,11]),
                 ExpectedStartDate=d(days=random.randint(0,90)),
                 ExpectedEndDate=d(days=random.randint(-90,90)),
                 Simple=0, VerificationRequired=1,
                 GroupId=random.choice(list(gids.values())),
                 DeveloperUserId=random.choice(list(user_ids.values())),
                 CreatorUserId=random.choice(list(user_ids.values())))

print(f"  ✅ {len(rfi_ids)} RFIs seeded")

# ── JOBS ───────────────────────────────────────────────────────────────

job_ids = []
for i in range(40):
    jid = uid()
    job_ids.append(jid)
    smart_insert('Jobs', Id=jid, JobNumber=f'JOB-{2025000+i:04d}',
                 Description=f'{random.choice(["PM","CM","ERT","MOD"])} - {random.choice(["Pump overhaul","Valve replacement"])}',
                 JobState=random.choice([1,2,3,4,5,6]),
                 GroupId=random.choice(list(gids.values())),
                 DepartmentId=random.choice(list(depts.values())))

# RFIJobs
rfi_job_ids = set()
for rid in random.sample(rfi_ids, min(35, len(rfi_ids))):
    for jid in random.sample(job_ids, random.randint(1, 3)):
        rj_id = uid()
        rfi_job_ids.add(rj_id)
        lo, lf = d(days=random.randint(1,90)), d(days=random.randint(0,89))
        smart_insert('RFIJobs', Id=rj_id, RFIId=rid, JobId=jid,
                     LinkingUserId=random.choice(list(user_ids.values())),
                     LinkingDate=lo, DeLinkingDate=lf,
                     SetToWorkDate=lo, WorkCompleteDate=lf,
                     PercentageComplete=random.randint(0,100),
                     RFIJobState=random.choice([1,2,3,4,5,6]))

print(f"  ✅ {len(rfi_job_ids)} RFI-Job links seeded")

# ── PADLOCKS & LOCKBOXES ──────────────────────────────────────────────

pl_ids = [smart_insert('PadLocks', Id=uid(), SerialNumber=f'LOCK-{random.randint(1000,9999)}',
                       PadLockType=random.randint(1,3),
                       Status=random.choice(['Available','InUse','Damaged']))
          for _ in range(30)]

lb_ids = [smart_insert('Lockboxes', Id=uid(), SerialNumber=f'BOX-{random.randint(100,999)}',
                       Description=f'Lock box set {i+1}')
          for i in range(10)]

print(f"  ✅ {len(pl_ids)} padlocks, {len(lb_ids)} lockboxes")

# ── RFI ISOLATIONS & LOCKS ────────────────────────────────────────────

for rid in random.sample(rfi_ids, min(40, len(rfi_ids))):
    for ipid in random.sample(ip_ids, random.randint(1, 5)):
        smart_insert('RFIIsolations', Id=uid(), RFIId=rid,
                     Name=f'ISO-{random.randint(1000,9999)}',
                     IsolationPointId=ipid,
                     RFIIsolationState=random.choice([1,2,3,4,5]))

for rid in random.sample(rfi_ids, min(30, len(rfi_ids))):
    for _ in range(random.randint(1, 5)):
        rl_id = uid()
        lo = d(days=random.randint(1,90), hours=random.randint(0,720))
        lf = d(days=random.randint(0,89), hours=random.randint(0,700))
        smart_insert('RFILocks', Id=rl_id, RFIId=rid,
                     UserId=random.choice(list(user_ids.values())),
                     PadLockId=random.choice(pl_ids),
                     RFILockState=random.choice([1,2,3]),
                     LockOnDate=lo, LockOffDate=lf,
                     LockOnComment='Lock applied', LockOffComment='Lock removed')
        for rj in random.sample(list(rfi_job_ids), min(2, len(rfi_job_ids))):
            smart_insert('RFILocksRFIJobs', Id=uid(), RFILockId=rl_id, RFIJobId=rj,
                         RFILockState=random.choice([1,2,3]),
                         LockOnDate=lo, LockOffDate=lf,
                         PercentageComplete=random.randint(0,100))

print("  ✅ RFI isolation & lock events seeded")

# ── RFI LOGS ───────────────────────────────────────────────────────────

for rid in rfi_ids:
    for _ in range(random.randint(2, 8)):
        smart_insert('RFILogs', Id=uid(), RFIId=rid,
                     Description=random.choice(['Status changed','Isolation applied','Work started','Work completed','Isolation removed','Verified']),
                     Comment=random.choice(['Completed','Pending','On hold','Approved','Rejected']),
                     RFILogType=random.randint(1,6),
                     UserId=random.choice(list(user_ids.values())))

print("  ✅ RFI logs seeded")

# ── ISOLATION POINT LOGS ──────────────────────────────────────────────

for ipid in ip_ids:
    for _ in range(random.randint(0, 5)):
        smart_insert('IsolationPointLogs', Id=uid(), IsolationPointId=ipid,
                     Description=random.choice(['Applied','Removed','Verified']),
                     IsolationPointLogType=random.randint(1,5),
                     UserId=random.choice(list(user_ids.values())))

print("  ✅ Isolation point logs seeded")

# ── WORK PERMITS ──────────────────────────────────────────────────────

for i in range(25):
    smart_insert('WorkPermits', Id=uid(),
                 WorkPermitTypeId=random.choice(list(wpts.values())),
                 RFIId=random.choice(rfi_ids),
                 Description=f'Permit for {random.choice(["hot work","cold work","confined space","height access","electrical isolation"])}',
                 State=random.choice([1,2,3,4,5,6]),
                 UserId=random.choice(list(user_ids.values())))

print("  ✅ Work permits seeded")

# ── AUDITS ─────────────────────────────────────────────────────────────

for i in range(15):
    aid = uid()
    smart_insert('Audits', Id=aid,
                 Name=f'Inspection {random.choice(["Q1","Q2","Q3","Q4"])} - {random.choice(["Electrical","Mechanical","Fire","Structural"])}',
                 Description=random.choice(['Routine inspection','Compliance audit','Annual review']),
                 AuditType=random.randint(1,4), AuditState=random.choice([1,2,3,4,5]),
                 EventStartDate=d(days=random.randint(30,90)),
                 EventEndDate=d(days=random.randint(0,29)),
                 Defects=random.choice([0,1]))
    for _ in range(random.randint(3, 10)):
        smart_insert('AuditChecks', Id=uid(), AuditId=aid,
                     AuditCheckType=random.randint(1,5),
                     DefectFound=random.choice([0,0,0,1]),
                     DefectDescription=random.choice(['','Guard missing','Label illegible']),
                     ActionsTaken=random.choice([0,0,1]),
                     ActionsDescription=random.choice(['','Replaced','Tightened']),
                     CheckQuestion=random.choice(['Is isolation labelled?','Is area clean?']),
                     AuditCheckDate=d(days=random.randint(1,180)))

print("  ✅ Audits seeded")

# ── TEMPORARY TAGS ─────────────────────────────────────────────────────

for _ in range(20):
    smart_insert('TemporaryTags', Id=uid(),
                 TemporaryTagNumber=f'TT-{random.randint(1000,9999)}',
                 TemporaryTagState=random.choice([1,2,3]),
                 Notes=random.choice(['Danger - Do not operate','Out of service','Maintenance']),
                 RFIId=random.choice(rfi_ids),
                 IsolationPointId=random.choice(ip_ids),
                 EquipmentId=random.choice(list(equip_ids.values())),
                 AppliedUserId=random.choice(list(user_ids.values())),
                 AppliedDate=d(days=random.randint(1,30)),
                 RemovalDate=d(days=random.randint(0,29)))

print("  ✅ Temporary tags seeded")

# ── EVENT LOGS ─────────────────────────────────────────────────────────

for i in range(500):
    smart_insert('EventLogs', Id=uid(),
                 UserId=random.choice(list(user_ids.values())) if random.random() < 0.8 else None,
                 EventLogArea=random.choice(['RFI','Isolation','User','Job','Audit','WorkPermit']),
                 EventLogOperations=random.choice([1,10,20,30,40,50,60,70,80,90]),
                 ObjectId=uid())

print("  ✅ Event logs seeded")

# ── COMMIT ─────────────────────────────────────────────────────────────

conn.commit()
conn.close()

print()
print("✅ Seeding complete!")
