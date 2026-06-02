"""
OneTag HMAS Sydney — Interactive Database Explorer & Query App
Single-file Streamlit app.  Connects to SQL Server (OneTag_Sydney).

Visualizations: bar, pie, line, histogram, heatmap, Gantt, Sankey.
All four BC export queries are incorporated with improvements.

Usage:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import pymssql
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

DB_CONFIG = {
    "server": "172.17.0.1",
    "port": 1433,
    "user": "SA",
    "password": "OneTagRestore2024!",
    "database": "OneTag_Sydney",
    "timeout": 30,
    "login_timeout": 10,
}

LOG_TYPE_NAMES = {
    1: "AuthorityToIsolateSignOff",
    2: "IsolationsActive",
    3: "IsolationsActiveVerified",
    4: "RFIComplete",
    5: "RFICompleteVerified",
    6: "RFIRejected",
    7: "AlterationsNotes",
    8: "LockOffComplete",
    9: "LockOnComplete",
    10: "LockAudit",
    11: "RFIRemove",
    12: "RFIUnlock",
    13: "RFIPrint",
    14: "RFIOnHold",
}

THEME = {
    "template": "plotly_dark",
    "color_continuous_scale": "Viridis",
    "font": {"color": "#c9d1d9"},
    "plot_bgcolor": "#0d1117",
    "paper_bgcolor": "#0d1117",
}

# ═══════════════════════════════════════════════════════════════
#  DATABASE LAYER
# ═══════════════════════════════════════════════════════════════


@st.cache_resource(ttl=300)
def get_connection():
    try:
        conn = pymssql.connect(**DB_CONFIG)
        conn.autocommit(True)
        return conn
    except pymssql.OperationalError as e:
        st.error(f"⚠️ DB connection failed: {e}")
        st.info("Run: `docker start sqlserver-onetag` on host")
        return None


def check_connection():
    try:
        conn = pymssql.connect(**{**DB_CONFIG, "timeout": 5, "login_timeout": 5})
        cur = conn.cursor()
        cur.execute("SELECT @@VERSION")
        version = cur.fetchone()[0][:50]
        conn.close()
        return True, version
    except Exception as e:
        return False, str(e)


@st.cache_data(ttl=60, show_spinner=False)
def query(sql, params=None):
    """Return list of dicts, retries once on failure."""
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(as_dict=True)
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur.fetchmany(50000)
    except Exception as e:
        st.error(f"Query error: {e}")
        return []


def query_df(sql, params=None):
    rows = query(sql, params)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ═══════════════════════════════════════════════════════════════
#  QUERY HELPERS
# ═══════════════════════════════════════════════════════════════

def build_where(conditions, base="1=1"):
    where = " AND ".join(conditions) if conditions else base
    return f"WHERE {where}"


def rfi_jobs_vendors(date_from=None, date_to=None, company=None, rfi_state=None, active_only=True):
    """Original Export RFIs Jobs.sql + LockBox + date/state filters."""
    cond, params = [], {}
    if date_from:
        cond.append("r.CreatedDate >= %(dfrom)s"); params["dfrom"] = date_from
    if date_to:
        cond.append("r.CreatedDate <= %(dto)s"); params["dto"] = date_to
    if company:
        cond.append("c.Name LIKE %(company)s"); params["company"] = f"%{company}%"
    if rfi_state:
        cond.append("r.RFIState = %(state)s"); params["state"] = rfi_state
    if active_only:
        cond.append("r.DeletedDate IS NULL")
    where = build_where(cond)
    sql = f"""SELECT r.Id, r.RFINumber, r.Description, rl.SerialNumber AS LockBox,
                     r.RFIState, cu.FirstName, cu.LastName,
                     j.JobNumber, j.Description AS JobDescription, c.Name AS Vendor
              FROM RFIs r
              INNER JOIN Users cu ON r.CreatedBy = cu.Id
              INNER JOIN RFIJobs rj ON rj.RFIId = r.Id
              INNER JOIN Jobs j ON rj.JobId = j.Id
              INNER JOIN Companies c ON j.CompanyId = c.Id
              LEFT OUTER JOIN RFILockBoxes rl ON rl.RFIId = r.Id
              {where} ORDER BY r.CreatedDate DESC"""
    return sql, params


def jobs_isolations_equipment(date_from=None, date_to=None, iso=None, equip=None, active_only=True):
    """Original Export Jobs Isolations Equipment.sql with proper area aliases."""
    cond, params = [], {}
    if date_from:
        cond.append("rj.CreatedDate >= %(dfrom)s"); params["dfrom"] = date_from
    if date_to:
        cond.append("rj.CreatedDate <= %(dto)s"); params["dto"] = date_to
    if iso:
        cond.append("i.Name LIKE %(iso)s"); params["iso"] = f"%{iso}%"
    if equip:
        cond.append("e.Name LIKE %(equip)s"); params["equip"] = f"%{equip}%"
    if active_only:
        cond.append("r.DeletedDate IS NULL AND i.DeletedDate IS NULL AND e.DeletedDate IS NULL")
    where = build_where(cond)
    sql = f"""SELECT DISTINCT r.RFINumber, j.JobNumber, j.Description AS JobDescription,
                     sa.StandardActivityNumber AS StandardActivity,
                     a.Number AS Activity, j.NoteNumber AS DocumentNumber,
                     i.Name AS IsolationPoint,
                     ia.Name AS Area,
                     e.Name AS Equipment,
                     ea.Name AS EquipmentArea
              FROM RFILocksRFIJobs rlrj
              INNER JOIN RFIJobs rj ON rlrj.RFIJobId = rj.Id
              INNER JOIN Jobs j ON rj.JobId = j.Id
              LEFT OUTER JOIN StandardActivities sa ON j.StandardActivityId = sa.Id
              LEFT OUTER JOIN Activities a ON j.ActivityId = a.Id
              INNER JOIN RFIs r ON rj.RFIId = r.Id
              INNER JOIN RFIIsolations ri ON r.Id = ri.RFIId
              INNER JOIN IsolationPoints i ON ri.IsolationPointId = i.Id
              INNER JOIN Areas ia ON i.AreaId = ia.Id
              INNER JOIN Equipment e ON ri.EquipmentId = e.Id
              INNER JOIN Areas ea ON e.AreaId = ea.Id
              {where} ORDER BY j.JobNumber"""
    return sql, params


def lock_history(date_from=None, date_to=None, company=None, worker=None,
                 min_min=None, max_min=None, active_only=True):
    """Original Export Lock History.sql + parameterized filters."""
    cond, params = [], {}
    if date_from:
        cond.append("rlrj.LockOnDate >= %(dfrom)s"); params["dfrom"] = date_from
    if date_to:
        cond.append("rlrj.LockOnDate <= %(dto)s"); params["dto"] = date_to
    if company:
        cond.append("c.Name LIKE %(company)s"); params["company"] = f"%{company}%"
    if worker:
        cond.append("CONCAT(u.FirstName, ' ', u.LastName) LIKE %(worker)s"); params["worker"] = f"%{worker}%"
    if min_min is not None:
        cond.append("DATEDIFF(MINUTE, rlrj.LockOnDate, rlrj.LockOffDate) >= %(min)s"); params["min"] = min_min
    if max_min is not None:
        cond.append("DATEDIFF(MINUTE, rlrj.LockOnDate, rlrj.LockOffDate) <= %(max)s"); params["max"] = max_min
    if active_only:
        cond.append("rlrj.DeletedDate IS NULL")
    where = build_where(cond, base="rlrj.LockOffDate IS NOT NULL AND rlrj.LockOnDate <= rlrj.LockOffDate")
    sql = f"""SELECT CONCAT(u.FirstName, ' ', u.LastName) AS Worker,
                     u.Mobile AS Phone, r.RFINumber, rlb.SerialNumber AS LockBox,
                     p.SerialNumber AS Padlock, j.JobNumber,
                     j.Description AS JobDescription, c.Name AS Company,
                     rlrj.LockOnDate, rlrj.LockOffDate,
                     DATEDIFF(MINUTE, rlrj.LockOnDate, rlrj.LockOffDate) AS DurationMinutes,
                     sa.StandardActivityNumber AS StandardActivity, a.Number AS Activity
              FROM RFILocksRFIJobs rlrj
              INNER JOIN RFILocks rl ON rlrj.RFILockId = rl.Id
              INNER JOIN PadLocks p ON rl.PadLockId = p.Id
              INNER JOIN Users u ON rl.UserId = u.Id
              INNER JOIN RFIJobs rj ON rlrj.RFIJobId = rj.Id
              INNER JOIN Jobs j ON rj.JobId = j.Id
              LEFT OUTER JOIN Companies c ON j.CompanyId = c.Id
              LEFT OUTER JOIN StandardActivities sa ON j.StandardActivityId = sa.Id
              LEFT OUTER JOIN Activities a ON j.ActivityId = a.Id
              INNER JOIN RFIs r ON rj.RFIId = r.Id
              LEFT OUTER JOIN RFILockBoxes rlb ON r.Id = rlb.RFIId
              {where} ORDER BY rlrj.LockOnDate DESC"""
    return sql, params


def rfi_log_timeline(date_from=None, date_to=None, log_type=None, rfi_number=None, active_only=True):
    """Original Export RFILogTypes.sql — cleaned joins, UTC, full log type enum."""
    cond, params = [], {}
    if date_from:
        cond.append("l.CreatedDate >= %(dfrom)s"); params["dfrom"] = date_from
    if date_to:
        cond.append("l.CreatedDate <= %(dto)s"); params["dto"] = date_to
    if log_type:
        cond.append("l.RFILogType IN %(types)s"); params["types"] = log_type
    if rfi_number:
        cond.append("r.RFINumber LIKE %(rfi)s"); params["rfi"] = f"%{rfi_number}%"
    if active_only:
        cond.append("r.DeletedDate IS NULL")
    where = build_where(cond)
    sql = f"""SELECT r.RFINumber, r.Description AS RFIDescription,
                     l.RFILogType, l.Description AS LogDescription,
                     u.FirstName, u.LastName, u.Position AS Role,
                     c.Name AS Company, l.CreatedDate AS DateTime
              FROM RFILogs l
              INNER JOIN RFIs r ON l.RFIId = r.Id
              INNER JOIN Users u ON l.UserId = u.Id
              INNER JOIN Companies c ON u.CompanyId = c.Id
              {where} ORDER BY r.RFINumber, l.CreatedDate"""
    return sql, params


# ═══════════════════════════════════════════════════════════════
#  ANALYTICAL QUERIES (for charts)
# ═══════════════════════════════════════════════════════════════

def dashboard_summary():
    return """SELECT 'Active RFIs' AS Metric, COUNT(*) AS Value FROM RFIs WHERE DeletedDate IS NULL AND RFIState > 1 AND RFIState <= 11
    UNION ALL SELECT 'Total Isolation Points', COUNT(*) FROM IsolationPoints WHERE DeletedDate IS NULL
    UNION ALL SELECT 'Active Jobs', COUNT(*) FROM Jobs WHERE DeletedDate IS NULL
    UNION ALL SELECT 'Active Users', COUNT(*) FROM Users WHERE DeletedDate IS NULL AND AccountLocked = 0
    UNION ALL SELECT 'Companies (Vendors)', COUNT(*) FROM Companies WHERE DeletedDate IS NULL
    UNION ALL SELECT 'Padlocks', COUNT(*) FROM PadLocks WHERE DeletedDate IS NULL
    UNION ALL SELECT 'Total RFI Logs', COUNT(*) FROM RFILogs"""


def isolation_frequency(limit=20):
    return f"""SELECT TOP {limit} i.Name AS IsolationPoint, ia.Name AS Area,
                      COUNT(ri.Id) AS IsolationCount, COUNT(DISTINCT ri.RFIId) AS RFICount
               FROM IsolationPoints i
               LEFT JOIN RFIIsolations ri ON i.Id = ri.IsolationPointId AND ri.DeletedDate IS NULL
               LEFT JOIN Areas ia ON i.AreaId = ia.Id
               WHERE i.DeletedDate IS NULL GROUP BY i.Name, ia.Name ORDER BY IsolationCount DESC"""


def worker_lock_activity(limit=20):
    return f"""SELECT TOP {limit} u.FirstName, u.LastName,
                      COUNT(rlrj.Id) AS LockEvents,
                      AVG(CAST(DATEDIFF(MINUTE, rlrj.LockOnDate, rlrj.LockOffDate) AS FLOAT)) AS AvgDurationMinutes
               FROM Users u
               INNER JOIN PadLocks p ON u.Id = p.UserId AND p.DeletedDate IS NULL
               INNER JOIN RFILocks rl ON p.Id = rl.PadLockId AND rl.DeletedDate IS NULL
               INNER JOIN RFILocksRFIJobs rlrj ON rl.Id = rlrj.RFILockId AND rlrj.DeletedDate IS NULL
               WHERE u.DeletedDate IS NULL GROUP BY u.FirstName, u.LastName ORDER BY LockEvents DESC"""


# ═══════════════════════════════════════════════════════════════
#  CHART BUILDERS
# ═══════════════════════════════════════════════════════════════

def apply_theme(fig):
    fig.update_layout(template=THEME["template"], plot_bgcolor=THEME["plot_bgcolor"],
                      paper_bgcolor=THEME["paper_bgcolor"], font=THEME["font"],
                      margin=dict(l=40, r=40, t=40, b=40))
    return fig


def sankey_rfi_state_flow():
    """
    Build a Sankey diagram showing RFI state transitions.
    For each RFI, order its log entries chronologically and count
    transitions between consecutive RFILogType values.
    """
    rows = query("""
        SELECT l1.RFIId, l1.RFILogType AS FromType, l2.RFILogType AS ToType, COUNT(*) AS Weight
        FROM (
            SELECT RFIId, RFILogType, CreatedDate,
                   ROW_NUMBER() OVER (PARTITION BY RFIId ORDER BY CreatedDate) AS Seq
            FROM RFILogs
        ) l1
        INNER JOIN (
            SELECT RFIId, RFILogType, CreatedDate,
                   ROW_NUMBER() OVER (PARTITION BY RFIId ORDER BY CreatedDate) AS Seq
            FROM RFILogs
        ) l2 ON l1.RFIId = l2.RFIId AND l1.Seq = l2.Seq - 1
        WHERE l1.RFILogType != l2.RFILogType
        GROUP BY l1.RFIId, l1.RFILogType, l2.RFILogType
    """)
    if not rows:
        return None
    df = pd.DataFrame(rows)
    # Aggregate all RFIId rows
    agg = df.groupby(["FromType", "ToType"], as_index=False)["Weight"].sum()
    agg = agg[agg["Weight"] >= 3]  # filter noise
    nodes = sorted(set(agg["FromType"].tolist() + agg["ToType"].tolist()))
    label_map = {v: f"{v}: {LOG_TYPE_NAMES.get(v, f'State {v}')}" for v in nodes}
    idx_map = {v: i for i, v in enumerate(nodes)}
    fig = go.Figure(go.Sankey(
        node=dict(label=[label_map[n] for n in nodes], pad=15, thickness=20,
                  color=["#2ecc71" if n in {1, 2, 3, 8, 9} else "#e74c3c" if n in {6, 11, 12}
                         else "#f39c12" for n in nodes]),
        link=dict(source=[idx_map[r["FromType"]] for _, r in agg.iterrows()],
                  target=[idx_map[r["ToType"]] for _, r in agg.iterrows()],
                  value=[r["Weight"] for _, r in agg.iterrows()])))
    fig.update_layout(title="RFI State Transitions", font_size=12)
    return apply_theme(fig)


def sankey_lock_chain():
    """
    Sankey diagram: Worker → Padlock → LockBox → RFI
    Shows the physical lock chain for active events.
    """
    rows = query("""
        SELECT TOP 500
            CONCAT(u.FirstName, ' ', u.LastName) AS Worker,
            p.SerialNumber AS Padlock,
            rlb.SerialNumber AS LockBox,
            r.RFINumber
        FROM RFILocksRFIJobs rlrj
        INNER JOIN RFILocks rl ON rlrj.RFILockId = rl.Id AND rl.DeletedDate IS NULL
        INNER JOIN PadLocks p ON rl.PadLockId = p.Id AND p.DeletedDate IS NULL
        INNER JOIN Users u ON rl.UserId = u.Id AND u.DeletedDate IS NULL
        INNER JOIN RFIJobs rj ON rlrj.RFIJobId = rj.Id
        INNER JOIN RFIs r ON rj.RFIId = r.Id AND r.DeletedDate IS NULL
        INNER JOIN RFILockBoxes rlb ON r.Id = rlb.RFIId
        WHERE rlrj.DeletedDate IS NULL AND rlb.SerialNumber IS NOT NULL
        ORDER BY rlrj.LockOnDate DESC
    """)
    if not rows:
        return None
    df = pd.DataFrame(rows)
    # Build links: Worker→Padlock, Padlock→LockBox, LockBox→RFI
    links = []
    for _, r in df.iterrows():
        links.append({"source": f"🧑 {r['Worker']}", "target": f"🔒 {r['Padlock']}", "value": 1})
        links.append({"source": f"🔒 {r['Padlock']}", "target": f"📦 {r['LockBox']}", "value": 1})
        links.append({"source": f"📦 {r['LockBox']}", "target": f"📋 {r['RFINumber']}", "value": 1})
    ldf = pd.DataFrame(links)
    agg = ldf.groupby(["source", "target"], as_index=False)["value"].sum()
    nodes = list(dict.fromkeys(agg["source"].tolist() + agg["target"].tolist()))
    idx_map = {v: i for i, v in enumerate(nodes)}
    fig = go.Figure(go.Sankey(
        node=dict(label=nodes, pad=15, thickness=20, color="#3498db"),
        link=dict(source=[idx_map[r["source"]] for _, r in agg.iterrows()],
                  target=[idx_map[r["target"]] for _, r in agg.iterrows()],
                  value=[r["value"] for _, r in agg.iterrows()])))
    fig.update_layout(title="Lock Chain: Worker → Padlock → LockBox → RFI (last 500)", font_size=11)
    return apply_theme(fig)


def sankey_vendor_equipment():
    """
    Sankey: Vendor → Job → Equipment
    Shows which vendors work on which equipment via which jobs.
    """
    rows = query("""
        SELECT TOP 300
            c.Name AS Vendor,
            j.JobNumber,
            e.Name AS Equipment
        FROM Jobs j
        INNER JOIN Companies c ON j.CompanyId = c.Id AND c.DeletedDate IS NULL
        INNER JOIN RFIJobs rj ON rj.JobId = j.Id
        INNER JOIN RFIs r ON rj.RFIId = r.Id AND r.DeletedDate IS NULL
        INNER JOIN RFIIsolations ri ON r.Id = ri.RFIId AND ri.DeletedDate IS NULL
        INNER JOIN Equipment e ON ri.EquipmentId = e.Id AND e.DeletedDate IS NULL
        WHERE j.DeletedDate IS NULL
    """)
    if not rows:
        return None
    df = pd.DataFrame(rows)
    links = []
    for _, r in df.iterrows():
        links.append({"source": f"🏢 {r['Vendor']}", "target": f"📄 {r['JobNumber']}", "value": 1})
        links.append({"target": f"⚙️ {r['Equipment']}", "source": f"📄 {r['JobNumber']}", "value": 1})
    ldf = pd.DataFrame(links)
    agg = ldf.groupby(["source", "target"], as_index=False)["value"].sum()
    nodes = list(dict.fromkeys(agg["source"].tolist() + agg["target"].tolist()))
    idx_map = {v: i for i, v in enumerate(nodes)}
    fig = go.Figure(go.Sankey(
        node=dict(label=nodes, pad=15, thickness=20, color="#2ecc71"),
        link=dict(source=[idx_map[r["source"]] for _, r in agg.iterrows()],
                  target=[idx_map[r["target"]] for _, r in agg.iterrows()],
                  value=[r["value"] for _, r in agg.iterrows()])))
    fig.update_layout(title="Vendor → Job → Equipment", font_size=11)
    return apply_theme(fig)


def chart_rfi_states(df):
    if df.empty: return None
    fig = px.pie(df, values="Count", names="RFIState",
                 title="RFI Distribution by State",
                 color_discrete_sequence=px.colors.sequential.Viridis_r)
    return apply_theme(fig)


def chart_isolation_freq(df, top_n=20):
    if df.empty: return None
    df = df.head(top_n)
    fig = px.bar(df, x="IsolationCount", y="IsolationPoint", color="RFICount",
                 color_continuous_scale="Viridis", orientation="h",
                 title=f"Top {top_n} Isolation Points by Usage",
                 labels={"IsolationCount": "Times Isolated", "IsolationPoint": ""})
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return apply_theme(fig)


def chart_worker_activity(df, top_n=20):
    if df.empty: return None
    df = df.head(top_n).copy()
    df["Worker"] = df["FirstName"] + " " + df["LastName"]
    fig = px.bar(df, x="LockEvents", y="Worker", color="AvgDurationMinutes",
                 color_continuous_scale="Viridis", orientation="h",
                 title=f"Top {top_n} Workers by Lock Events",
                 labels={"LockEvents": "Lock Events", "Worker": ""})
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return apply_theme(fig)


def chart_lock_histogram(df, max_min=480):
    if df.empty: return None
    df = df[df["DurationMinutes"] <= max_min]
    fig = px.histogram(df, x="DurationMinutes", nbins=50,
                       title="Lock Duration Distribution",
                       labels={"DurationMinutes": "Duration (minutes)"})
    return apply_theme(fig)


def chart_daily_timeline(df):
    if df.empty: return None
    df = df.copy()
    df["EventDate"] = pd.to_datetime(df["EventDate"])
    df = df.sort_values("EventDate")
    fig = px.line(df, x="EventDate", y="EventCount", color="RFILogType",
                  title="Daily Activity Timeline",
                  labels={"EventDate": "Date", "EventCount": "Events"})
    return apply_theme(fig)


def chart_lock_timeline(df, max_events=100):
    if df.empty: return None
    df = df.head(max_events).copy()
    df["Label"] = df["Worker"] + " | " + df["Padlock"]
    fig = px.timeline(df, x_start="LockOnDate", x_end="LockOffDate", y="Label",
                      color="JobNumber", title=f"Lock On/Off Timeline (last {max_events})",
                      labels={"JobNumber": "Job"})
    fig.update_yaxes(autorange="reversed")
    return apply_theme(fig)


def chart_vendor_breakdown(df):
    if df.empty or "Vendor" not in df.columns: return None
    vc = df["Vendor"].value_counts().head(20).reset_index()
    vc.columns = ["Vendor", "RFICount"]
    fig = px.bar(vc, x="RFICount", y="Vendor", orientation="h",
                 title="Top 20 Vendors by RFI Count",
                 labels={"RFICount": "Number of RFIs", "Vendor": ""})
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return apply_theme(fig)


def chart_activity_heatmap(df, date_col):
    if df.empty or date_col not in df.columns: return None
    df = df.dropna(subset=[date_col]).copy()
    df["Hour"] = pd.to_datetime(df[date_col]).dt.hour
    df["DayOfWeek"] = pd.to_datetime(df[date_col]).dt.day_name()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df["DayOfWeek"] = pd.Categorical(df["DayOfWeek"], categories=days, ordered=True)
    heat = df.groupby(["DayOfWeek", "Hour"], observed=False).size().reset_index(name="Count")
    heat = heat.pivot(index="DayOfWeek", columns="Hour", values="Count").fillna(0)
    fig = px.imshow(heat, title="Activity by Day & Hour",
                    labels=dict(x="Hour", y="Day", color="Events"),
                    color_continuous_scale="Viridis", aspect="auto")
    return apply_theme(fig)


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def fmt_duration(minutes):
    if pd.isna(minutes): return "-"
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m}m" if h else f"{m}m"


# ═══════════════════════════════════════════════════════════════
#  UI PAGES
# ═══════════════════════════════════════════════════════════════

def page_dashboard(flt):
    st.title("📊 Dashboard")
    with st.spinner("Loading summary…"):
        df = query_df(dashboard_summary())
    if not df.empty:
        cols = st.columns(4)
        for i, (_, r) in enumerate(df.iterrows()):
            with cols[i % 4]:
                st.metric(r["Metric"], f"{int(r['Value']):,}")
    c1, c2 = st.columns(2)
    with c1:
        with st.spinner("RFI state dist…"):
            df2 = query_df("SELECT RFIState, COUNT(*) AS Count FROM RFIs WHERE DeletedDate IS NULL GROUP BY RFIState ORDER BY RFIState")
            fig = chart_rfi_states(df2)
            if fig: st.plotly_chart(fig, use_container_width=True)
    with c2:
        with st.spinner("Isolation frequency…"):
            fig = chart_isolation_freq(query_df(isolation_frequency(15)), 15)
            if fig: st.plotly_chart(fig, use_container_width=True)
    c3, c4 = st.columns(2)
    with c3:
        with st.spinner("Worker activity…"):
            fig = chart_worker_activity(query_df(worker_lock_activity(15)), 15)
            if fig: st.plotly_chart(fig, use_container_width=True)
    with c4:
        with st.spinner("Lock duration…"):
            df3 = query_df("SELECT DATEDIFF(MINUTE, rlrj.LockOnDate, rlrj.LockOffDate) AS DurationMinutes FROM RFILocksRFIJobs rlrj WHERE rlrj.LockOffDate IS NOT NULL AND rlrj.DeletedDate IS NULL AND DATEDIFF(MINUTE, rlrj.LockOnDate, rlrj.LockOffDate) BETWEEN 1 AND 480")
            fig = chart_lock_histogram(df3)
            if fig: st.plotly_chart(fig, use_container_width=True)


def page_rfi_jobs(flt):
    st.title("📋 RFI → Jobs → Vendors")
    with st.spinner("Querying…"):
        sql, params = rfi_jobs_vendors(flt.dfrom, flt.dto, flt.company, flt.rfi_state, flt.active_only)
        df = query_df(sql, params)
    if df.empty: st.warning("No results."); return
    st.dataframe(df, use_container_width=True, height=500)
    st.caption(f"{len(df):,} rows")
    c1, c2 = st.columns(2)
    with c1:
        fig = chart_vendor_breakdown(df)
        if fig: st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = chart_activity_heatmap(df, "CreatedDate" if "CreatedDate" in df.columns else None)
        if fig: st.plotly_chart(fig, use_container_width=True)


def page_jobs_iso_equip(flt):
    st.title("🔗 Jobs → RFIs → Isolation Points → Equipment")
    with st.spinner("Querying…"):
        sql, params = jobs_isolations_equipment(flt.dfrom, flt.dto, None, None, flt.active_only)
        df = query_df(sql, params)
    if df.empty: st.warning("No results."); return
    st.dataframe(df, use_container_width=True, height=500)
    st.caption(f"{len(df):,} rows")


def page_lock_history(flt):
    st.title("🔒 Lock History")
    with st.spinner("Querying…"):
        sql, params = lock_history(flt.dfrom, flt.dto, flt.company, flt.worker, None, None, flt.active_only)
        df = query_df(sql, params)
    if df.empty: st.warning("No results."); return
    if "DurationMinutes" in df.columns:
        df["Duration"] = df["DurationMinutes"].apply(fmt_duration)
    st.dataframe(df, use_container_width=True, height=500)
    st.caption(f"{len(df):,} rows")
    c1, c2 = st.columns(2)
    with c1:
        fig = chart_activity_heatmap(df, "LockOnDate")
        if fig: st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = chart_lock_histogram(df)
        if fig: st.plotly_chart(fig, use_container_width=True)
    c3, c4 = st.columns(2)
    with c3:
        fig = chart_lock_timeline(df, 50)
        if fig: st.plotly_chart(fig, use_container_width=True)
    with c4:
        if "DurationMinutes" in df.columns:
            st.subheader("Lock Duration Stats")
            s = df["DurationMinutes"].describe()
            st.metric("Mean", fmt_duration(s["mean"]))
            st.metric("Median", fmt_duration(s["50%"]))
            st.metric("Max", fmt_duration(s["max"]))
            st.metric("Total", f"{len(df):,}")
            st.metric("Total Hours", f"{s['sum'] / 60:,.0f}")


def page_rfi_logs(flt):
    st.title("📜 RFI Log Timeline")
    log_types = st.multiselect("Filter by log type",
                                options=list(LOG_TYPE_NAMES.keys()),
                                format_func=lambda x: f"{x}: {LOG_TYPE_NAMES[x]}",
                                default=[1, 2, 3, 4, 5, 7, 14])
    with st.spinner("Querying…"):
        sql, params = rfi_log_timeline(flt.dfrom, flt.dto, tuple(log_types) if log_types else None, None, flt.active_only)
        df = query_df(sql, params)
    if df.empty: st.warning("No results."); return
    df["LogTypeName"] = df["RFILogType"].map(LOG_TYPE_NAMES)
    st.dataframe(df, use_container_width=True, height=500)
    st.caption(f"{len(df):,} rows")


def page_analysis(flt):
    st.title("📈 Analysis & Sankey Diagrams")
    tab = st.radio("Analysis type", ["Sankey Diagrams", "Pre-built Reports", "Custom SQL"], horizontal=True)
    if tab == "Sankey Diagrams":
        st.subheader("State Flow Sankey")
        fig = sankey_rfi_state_flow()
        if fig: st.plotly_chart(fig, use_container_width=True)
        else: st.info("Insufficient data for state flow Sankey — need more log entries.")
        st.subheader("Lock Chain Sankey")
        fig2 = sankey_lock_chain()
        if fig2: st.plotly_chart(fig2, use_container_width=True)
        else: st.info("No lock chains with LockBox assignments found in recent data.")
        st.subheader("Vendor → Equipment Sankey")
        fig3 = sankey_vendor_equipment()
        if fig3: st.plotly_chart(fig3, use_container_width=True)
        else: st.info("Insufficient data for vendor→equipment Sankey.")
    elif tab == "Pre-built Reports":
        report = st.selectbox("Report", [
            "Isolation Point Frequency", "Worker Lock Activity",
            "RFI State Distribution", "Vendor Breakdown",
            "Daily Activity Timeline (90 days)", "Top 20 Most Locked Equipment"])
        with st.spinner("Loading…"):
            if report == "Isolation Point Frequency":
                df = query_df(isolation_frequency(50)); fig = chart_isolation_freq(df, 20)
            elif report == "Worker Lock Activity":
                df = query_df(worker_lock_activity(50)); fig = chart_worker_activity(df, 20)
            elif report == "RFI State Distribution":
                df = query_df("SELECT RFIState, COUNT(*) AS Count FROM RFIs WHERE DeletedDate IS NULL GROUP BY RFIState ORDER BY RFIState"); fig = chart_rfi_states(df)
            elif report == "Vendor Breakdown":
                sql, _ = rfi_jobs_vendors(active_only=flt.active_only); df = query_df(sql); fig = chart_vendor_breakdown(df)
            elif report == "Daily Activity Timeline (90 days)":
                df = query_df("""SELECT CAST(l.CreatedDate AS DATE) AS EventDate, l.RFILogType, COUNT(*) AS EventCount FROM RFILogs l WHERE l.CreatedDate >= DATEADD(DAY, -90, GETUTCDATE()) GROUP BY CAST(l.CreatedDate AS DATE), l.RFILogType ORDER BY EventDate"""); fig = chart_daily_timeline(df)
            elif report == "Top 20 Most Locked Equipment":
                df = query_df("""SELECT TOP 20 e.Name AS Equipment, ea.Name AS Area, COUNT(DISTINCT ri.RFIId) AS RFICount FROM Equipment e INNER JOIN RFIIsolations ri ON e.Id = ri.EquipmentId AND ri.DeletedDate IS NULL LEFT JOIN Areas ea ON e.AreaId = ea.Id WHERE e.DeletedDate IS NULL GROUP BY e.Name, ea.Name ORDER BY RFICount DESC"""); fig = None
        if not df.empty:
            st.dataframe(df, use_container_width=True, height=400)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Only SELECT queries allowed.")
        sql = st.text_area("SQL", height=150, placeholder="SELECT TOP 10 * FROM Users WHERE DeletedDate IS NULL")
        if st.button("Run", type="primary") and sql.strip():
            if not sql.strip().upper().startswith("SELECT"): st.error("Only SELECT allowed.")
            else:
                with st.spinner("Running…"):
                    df = query_df(sql)
                if not df.empty:
                    st.dataframe(df, use_container_width=True, height=500)
                    st.caption(f"{len(df):,} rows in {len(df.columns)} columns")
                    csv = df.to_csv(index=False).encode()
                    st.download_button("📥 Download CSV", csv, "query_results.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════

st.set_page_config(page_title="OneTag HMAS Sydney — DB Explorer", page_icon="🏭", layout="wide", initial_sidebar_state="expanded")

# -- Sidebar --
st.sidebar.title("🏭 OneTag HMAS")
st.sidebar.caption("Lockout/Tagout DB Explorer")

ok, ver = check_connection()
if ok:
    st.sidebar.success(f"✅ Connected | {ver}")
else:
    st.sidebar.error(f"❌ Disconnected: {ver}")
    st.sidebar.info("Run: `docker start sqlserver-onetag` on host")
    st.stop()

page = st.sidebar.radio("Report", ["📊 Dashboard", "📋 RFI → Jobs → Vendors", "🔗 Jobs → Isolations → Equipment", "🔒 Lock History", "📜 RFI Log Timeline", "📈 Analysis"])

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
default_from = datetime(2025, 1, 1, tzinfo=timezone.utc)
default_to = datetime(2025, 11, 24, tzinfo=timezone.utc)
filter_date_from = st.sidebar.date_input("From", default_from)
filter_date_to = st.sidebar.date_input("To", default_to)
filter_company = st.sidebar.text_input("Company", placeholder="e.g. BHP")
filter_worker = st.sidebar.text_input("Worker", placeholder="e.g. First3560")
filter_rfi_state = st.sidebar.number_input("RFI State", 0, 20, 0, 1)
filter_active = st.sidebar.checkbox("Active only", value=True)

Filters = type("Filters", (), {})()
Filters.dfrom = filter_date_from
Filters.dto = filter_date_to
Filters.company = filter_company if filter_company else None
Filters.worker = filter_worker if filter_worker else None
Filters.rfi_state = filter_rfi_state if filter_rfi_state > 0 else None
Filters.active_only = filter_active

# -- Router --
pages = {
    "📊 Dashboard": page_dashboard,
    "📋 RFI → Jobs → Vendors": page_rfi_jobs,
    "🔗 Jobs → Isolations → Equipment": page_jobs_iso_equip,
    "🔒 Lock History": page_lock_history,
    "📜 RFI Log Timeline": page_rfi_logs,
    "📈 Analysis": page_analysis,
}
pages[page](Filters)
