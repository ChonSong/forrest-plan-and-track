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

import hmac as _hmac
import hashlib as _hashlib
_AUTH_USER = "sa"
_AUTH_PASS = "dawnofdarren"
_SECRET = _hashlib.sha256(b"onetag-hmas-sydney-2026").hexdigest()
_COOKIE_NAME = "session"
_COOKIE_VALUE = _hmac.new(_SECRET.encode(), _AUTH_USER.encode(), _hashlib.sha256).hexdigest()[:16]
def _get_cookie():
    try:
        cookies = st.context.headers.get("Cookie", "")
        for part in cookies.split(";"):
            part = part.strip()
            if part.startswith(_COOKIE_NAME + "="):
                val = part.split("=", 1)[1].strip()
                if val == _COOKIE_VALUE:
                    return True
    except Exception:
        pass
    return False
def _check_session():
    return st.session_state.get("_authenticated", False)
if not _get_cookie() and not _check_session():
    st.set_page_config(page_title="OneTag \u2014 Login", page_icon="\U0001f3ed", layout="centered")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("\U0001f3ed OneTag HMAS Sydney")
        st.subheader("Database Explorer \u2014 Log in to continue")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", use_container_width=True)
            if submitted:
                if username == _AUTH_USER and password == _AUTH_PASS:
                    st.session_state["_authenticated"] = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    st.stop()
if _get_cookie() and not _check_session():
    st.session_state["_authenticated"] = True


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


def _new_connection():
    """Create a fresh DB connection every time (no stale cached connections)."""
    for attempt in range(3):
        try:
            conn = pymssql.connect(**DB_CONFIG)
            conn.autocommit(True)
            return conn
        except pymssql.OperationalError:
            if attempt < 2:
                import time
                time.sleep(2)
    return None


def get_connection():
    """Legacy wrapper — kept for any direct callers."""
    return _new_connection()


def check_connection():
    conn = _new_connection()
    if conn is None:
        return False, "Cannot connect"
    try:
        cur = conn.cursor()
        cur.execute("SELECT @@VERSION")
        version = cur.fetchone()[0][:50]
        conn.close()
        return True, version
    except Exception as e:
        return False, str(e)


@st.cache_data(ttl=60, show_spinner=False)
def query(sql, params=None):
    """Return list of dicts. Opens a fresh connection each time to avoid timeouts."""
    conn = _new_connection()
    if conn is None:
        st.error("⚠️ Cannot connect to SQL Server. Run: `docker start sqlserver-onetag`")
        return []
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params) if params else cur.execute(sql)
        return cur.fetchmany(50000)
    except pymssql.OperationalError:
        # One retry with fresh connection
        conn2 = _new_connection()
        if conn2 is None:
            st.error("⚠️ DB connection lost and retry failed.")
            return []
        try:
            cur = conn2.cursor(as_dict=True)
            cur.execute(sql, params) if params else cur.execute(sql)
            return cur.fetchmany(50000)
        except Exception as e:
            st.error(f"Query error: {e}")
            return []
    except Exception as e:
        st.error(f"Query error: {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


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
    sql = f"""SELECT DISTINCT TOP 50 r.RFINumber, j.JobNumber, j.Description AS JobDescription,
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


def jobs_isolations_gantt_query(date_from=None, date_to=None, active_only=True):
    """Combined query: Jobs (actual lock dates) + Isolations (AppliedDate/RemovalDate).
    Returns one row per RFIIsolation, with job-level dates repeated.
    CTE avoids cross-product between lock events and isolations.
    Filters Gantt-invalid data (0001-01-01, start > end)."""
    cond, params = [], {}
    if date_from:
        cond.append("ri.AppliedDate >= %(dfrom)s"); params["dfrom"] = date_from
    if date_to:
        cond.append("(ri.RemovalDate <= %(dto)s OR ri.RemovalDate IS NULL)"); params["dto"] = date_to
    if active_only:
        cond.append("j.DeletedDate IS NULL AND r.DeletedDate IS NULL "
                     "AND ri.DeletedDate IS NULL AND i.DeletedDate IS NULL AND e.DeletedDate IS NULL")
    where = build_where(cond)
    sql = f"""WITH JobDateRange AS (
    SELECT rj.JobId,
           MIN(rlrj.LockOnDate) AS LockStart,
           MAX(rlrj.LockOffDate) AS LockEnd
    FROM RFIJobs rj
    LEFT JOIN RFILocksRFIJobs rlrj ON rlrj.RFIJobId = rj.Id AND rlrj.DeletedDate IS NULL
    WHERE rj.DeletedDate IS NULL
    GROUP BY rj.JobId
)
SELECT j.Id AS JobId,
       j.JobNumber, j.Description AS JobDescription,
       j.JobState, j.OnHold, c.Name AS Vendor,
       j.CreatedDate AS JobCreated,
       jdr.LockStart, jdr.LockEnd,
       r.RFINumber, r.Description AS RFIDescription,
       ri.Id AS IsolationId,
       i.Name AS IsolationPoint,
       ia.Name AS Area,
       e.Name AS Equipment,
       ri.AppliedDate AS IsoStart,
       ri.RemovalDate AS IsoEnd,
       ri.RFIIsolationState,
       CASE WHEN ri.RemovalDate IS NULL THEN 'Active' ELSE 'Removed' END AS IsoStatus
FROM Jobs j
INNER JOIN Companies c ON j.CompanyId = c.Id
INNER JOIN RFIJobs rj ON rj.JobId = j.Id AND rj.DeletedDate IS NULL
INNER JOIN RFIs r ON rj.RFIId = r.Id AND r.DeletedDate IS NULL
INNER JOIN RFIIsolations ri ON r.Id = ri.RFIId AND ri.DeletedDate IS NULL
    AND ri.AppliedDate IS NOT NULL
    AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
INNER JOIN IsolationPoints i ON ri.IsolationPointId = i.Id AND i.DeletedDate IS NULL
INNER JOIN Areas ia ON i.AreaId = ia.Id
INNER JOIN Equipment e ON ri.EquipmentId = e.Id AND e.DeletedDate IS NULL
LEFT JOIN JobDateRange jdr ON jdr.JobId = j.Id
{where}
ORDER BY jdr.LockStart DESC NULLS LAST, j.JobNumber, ri.AppliedDate"""
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


def chart_lock_timeline(df, max_events=100):
    if df.empty: return None
    df = df.head(max_events).copy()
    df = df.dropna(subset=["LockOnDate", "LockOffDate"]).copy()
    if df.empty:
        return None
    df = df[df["LockOnDate"] <= df["LockOffDate"]].copy()
    if df.empty:
        return None
    df["Label"] = df["Worker"] + " | " + df["Padlock"]
    fig = px.timeline(df, x_start="LockOnDate", x_end="LockOffDate", y="Label",
                      color="JobNumber", title=f"Lock On/Off Timeline (last {max_events})",
                      labels={"JobNumber": "Job"})
    fig.update_yaxes(autorange="reversed")
    # Force x-axis to show all data — px.timeline's auto-range can clip bars
    min_d = df["LockOnDate"].min()
    max_d = df["LockOffDate"].max()
    if pd.notna(min_d) and pd.notna(max_d) and max_d > min_d:
        pad = (max_d - min_d) * 0.03
        fig.update_xaxes(range=[min_d - pad, max_d + pad])
    # Range slider for interactive zoom
    fig.update_xaxes(rangeslider_visible=True, rangeslider_thickness=0.05)
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


def chart_jobs_isolations_gantt(df, top_n=25, search_term=None):
    """Combined parent-child Gantt: Jobs (lock dates) as parent bars,
    Isolations (AppliedDate→RemovalDate) as child bars underneath."""
    if df.empty:
        return None

    # Build unified records preserving job→isolation hierarchy
    records = []
    jobs_df = df[["JobNumber", "JobDescription", "Vendor", "JobState",
                  "LockStart", "LockEnd"]].drop_duplicates("JobNumber")
    jobs_df = jobs_df.dropna(subset=["LockStart", "LockEnd"])
    jobs_df = jobs_df[jobs_df["LockStart"] <= jobs_df["LockEnd"]]
    if jobs_df.empty:
        return None

    if search_term:
        mask = (jobs_df["JobDescription"].str.contains(search_term, case=False, na=False) |
                jobs_df["JobNumber"].str.contains(search_term, case=False, na=False))
        jobs_df = jobs_df[mask]
    if jobs_df.empty:
        return None

    jobs_df = jobs_df.sort_values("LockStart", ascending=False).head(top_n)

    state_labels = {0: "Cancelled", 1: "Active", 2: "Completed"}
    for _, job in jobs_df.iterrows():
        s = state_labels.get(job.get("JobState"), "Unknown")
        records.append({
            "Task": f"📋 {job['JobNumber']}: {str(job['JobDescription'])[:50]}",
            "Start": job["LockStart"], "End": job["LockEnd"],
            "Color": s, "Type": "Job",
            "Detail": job["Vendor"],
        })
        iso_sub = df[df["JobNumber"] == job["JobNumber"]].copy()
        iso_sub = iso_sub.dropna(subset=["IsoStart"])
        for _, iso in iso_sub.iterrows():
            e = iso["IsoEnd"] if pd.notna(iso["IsoEnd"]) else iso["IsoStart"] + pd.Timedelta(hours=1)
            if iso["IsoStart"] <= e:
                records.append({
                    "Task": f"  └─ {iso['IsolationPoint']} ({iso['Equipment']})",
                    "Start": iso["IsoStart"], "End": e,
                    "Color": "Removed" if iso["IsoStatus"] == "Removed" else "Active",
                    "Type": "Isolation",
                    "Detail": f"{iso['Area']} | {iso['RFINumber']}",
                })

    if not records:
        return None

    plot_df = pd.DataFrame(records)
    color_map = {"Completed": "#2ecc71", "Active": "#3498db",
                 "Removed": "#95a5a6", "Cancelled": "#e74c3c"}

    fig = px.timeline(
        plot_df, x_start="Start", x_end="End", y="Task",
        color="Color", color_discrete_map=color_map,
        title=f"Jobs & Isolations Timeline (top {top_n} jobs)",
        labels={"Task": "", "Color": "Status"},
        hover_data={"Type": True, "Detail": True, "Start": "|%Y-%m-%d", "End": "|%Y-%m-%d"},
        category_orders={"Color": ["Completed", "Active", "Removed", "Cancelled"]},
    )
    fig.update_yaxes(autorange="reversed", categoryorder="array",
                     categoryarray=[r["Task"] for r in records])
    fig.update_layout(height=max(500, len(records) * 20))
    # Fix x-axis range
    mn, mx = plot_df["Start"].min(), plot_df["End"].max()
    if pd.notna(mn) and pd.notna(mx) and mx > mn:
        fig.update_xaxes(range=[mn - (mx - mn) * 0.02, mx + (mx - mn) * 0.02])
    return apply_theme(fig)


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def show_sql(sql, label="SQL Query"):
    """Display a collapsible SQL query section."""
    with st.expander(f"📝 {label}", expanded=False):
        st.code(sql, language="sql")


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
            if fig: st.plotly_chart(fig, width='stretch')
    with c2:
        with st.spinner("Isolation frequency…"):
            fig = chart_isolation_freq(query_df(isolation_frequency(15)), 15)
            if fig: st.plotly_chart(fig, width='stretch')
    c3, c4 = st.columns(2)
    with c3:
        with st.spinner("Worker activity…"):
            fig = chart_worker_activity(query_df(worker_lock_activity(15)), 15)
            if fig: st.plotly_chart(fig, width='stretch')
    with c4:
        with st.spinner("Lock duration…"):
            df3 = query_df("SELECT DATEDIFF(MINUTE, rlrj.LockOnDate, rlrj.LockOffDate) AS DurationMinutes FROM RFILocksRFIJobs rlrj WHERE rlrj.LockOffDate IS NOT NULL AND rlrj.DeletedDate IS NULL AND DATEDIFF(MINUTE, rlrj.LockOnDate, rlrj.LockOffDate) BETWEEN 1 AND 480")
            fig = chart_lock_histogram(df3)
            if fig: st.plotly_chart(fig, width='stretch')


def page_rfi_jobs(flt):
    st.title("📋 RFI → Jobs → Vendors")
    with st.spinner("Querying…"):
        sql, params = rfi_jobs_vendors(flt.dfrom, flt.dto, flt.company, flt.rfi_state, flt.active_only)
        df = query_df(sql, params)
    if df.empty: st.warning("No results."); return
    st.dataframe(df, use_container_width=True, height=500)
    st.caption(f"{len(df):,} rows")
    show_sql(sql, "RFI → Jobs → Vendors Query")
    c1, c2 = st.columns(2)
    with c1:
        fig = chart_vendor_breakdown(df)
        if fig: st.plotly_chart(fig, width='stretch')
    with c2:
        fig = chart_activity_heatmap(df, "CreatedDate" if "CreatedDate" in df.columns else None)
        if fig: st.plotly_chart(fig, width='stretch')


def page_jobs_iso_equip(flt):
    st.title("🔗 Jobs → RFIs → Isolation Points → Equipment")
    with st.spinner("Querying…"):
        sql, params = jobs_isolations_equipment(flt.dfrom, flt.dto, None, None, flt.active_only)
        df = query_df(sql, params)
    if df.empty: st.warning("No results."); return
    st.dataframe(df, use_container_width=True, height=500)
    st.caption(f"{len(df):,} rows")
    show_sql(sql, "Jobs → Isolations → Equipment Query")


def page_lock_history(flt):
    st.title("🔒 Lock History")
    
    # Duration filter checkbox
    filter_negative = st.checkbox("Filter out DurationMinutes < -1 (bad data)", value=True)
    
    with st.spinner("Querying…"):
        sql, params = lock_history(flt.dfrom, flt.dto, flt.company, flt.worker, None, None, flt.active_only)
        df = query_df(sql, params)
    if df.empty: st.warning("No results."); return
    
    # Apply DurationMinutes filter
    if filter_negative and "DurationMinutes" in df.columns:
        before = len(df)
        df = df[df["DurationMinutes"] >= -1]
        filtered = before - len(df)
        if filtered > 0:
            st.caption(f"⚠️ Filtered out {filtered} rows with DurationMinutes < -1")
    
    if "DurationMinutes" in df.columns:
        df["Duration"] = df["DurationMinutes"].apply(fmt_duration)
    st.dataframe(df, use_container_width=True, height=500)
    st.caption(f"{len(df):,} rows")
    show_sql(sql, "Lock History Query")
    c1, c2 = st.columns(2)
    with c1:
        fig = chart_activity_heatmap(df, "LockOnDate")
        if fig: st.plotly_chart(fig, width='stretch')
    with c2:
        fig = chart_lock_histogram(df)
        if fig: st.plotly_chart(fig, width='stretch')
    c3, c4 = st.columns(2)
    with c3:
        fig = chart_lock_timeline(df, 50)
        if fig: st.plotly_chart(fig, width='stretch')
    with c4:
        if "DurationMinutes" in df.columns:
            st.subheader("Lock Duration Stats")
            s = df["DurationMinutes"].describe()
            st.metric("Mean", fmt_duration(s["mean"]))
            st.metric("Median", fmt_duration(s["50%"]))
            st.metric("Max", fmt_duration(s["max"]))
            st.metric("Total", f"{len(df):,}")
            st.metric("Total Hours", f"{df['DurationMinutes'].sum() / 60:,.0f}")


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
    show_sql(sql, "RFI Log Timeline Query")


def page_analysis(flt):
    st.title("📈 Analysis & Sankey Diagrams")
    st.warning("⚠️ This page is currently under development and has been disabled to prevent system overload.")

    st.markdown("""
    ### Planned Features

    **Sankey Diagrams**
    - **RFI State Flow** — Visualize how RFIs transition between states (created → isolated → verified → complete)
    - **Lock Chain** — Trace the physical lock chain: Worker → Padlock → LockBox → RFI
    - **Vendor → Equipment** — Map which vendors work on which equipment through jobs

    **Pre-built Reports**
    - Isolation Point Frequency — Most-used isolation points ranked by usage
    - Worker Lock Activity — Top workers by lock event count and average duration
    - RFI State Distribution — Pie chart breakdown of RFI states
    - Vendor Breakdown — Top 20 vendors by RFI count
    - Daily Activity Timeline — 90-day trend of log events by type
    - Top 20 Most Locked Equipment — Equipment ranked by distinct RFI count

    **Ad-Hoc SQL**
    - Custom read-only SQL queries with CSV download

    These features will be re-enabled once query performance is optimized.
    """)


def page_findings(flt):
    """Forrest Analysis Engine — Findings page."""
    st.title("🚀 Forrest Findings")
    st.caption("Automated anomaly, pattern, and relationship detection over the OneTag HMAS data")

    # Connect to local SQLite DB
    import os as _os
    _db_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'data', 'onetag.db')
    if not _os.path.exists(_db_path):
        st.error(f"Local database not found at {_db_path}")
        st.info("Run `python scripts/seed_data.py` from the repo root to create it.")
        return

    col1, col2 = st.columns([3, 1])
    with col2:
        run_btn = st.button("▶️ Run Analysis", type="primary", use_container_width=True)

    with col1:
        top_n = st.slider("Findings to display", 3, 20, 10, help="Number of top findings to show")

    # Cache the result — re-run only when button is clicked
    @st.cache_data(ttl=3600, show_spinner="Running Forrest analysis passes…")
    def _run_forrest():
        import sys as _sys
        # Ensure the repo root is in path for engine imports
        _repo_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if _repo_root not in _sys.path:
            _sys.path.insert(0, _repo_root)
        import sqlite3 as _sqlite3
        _conn = _sqlite3.connect(_db_path)
        _conn.row_factory = _sqlite3.Row
        from engine.runner import run_all as _run_all
        _result = _run_all(_conn)
        _conn.close()
        return _result

    if run_btn:
        st.cache_data.clear()

    try:
        result = _run_forrest()
    except Exception as e:
        st.error(f"Analysis engine failed: {e}")
        st.info("Make sure the engine package is installed (run from repo root, not streamlit_onetag/)")
        return

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Analysis Passes", result.passes_run)
    c2.metric("Total Findings", result.total_findings)
    c3.metric("Runtime", f"{result.duration_seconds:.2f}s")
    best = result.top(1)
    c4.metric("Top Score", f"{best[0].score:.3f}" if best else "—")

    st.markdown("---")

    if result.total_findings == 0:
        st.info("No findings were generated. The seeded data may be too uniform — try running with more data.")
        return

    # Display findings
    top_findings = result.top(top_n)
    for i, f in enumerate(top_findings, 1):
        sev_color = "#e74c3c" if f.score >= 0.6 else ("#f39c12" if f.score >= 0.4 else "#2ecc71")
        sev_label = "🔴 Critical" if f.score >= 0.6 else ("🟡 Moderate" if f.score >= 0.4 else "🟢 Minor")

        with st.container(border=True):
            cols = st.columns([0.05, 0.7, 0.25])
            with cols[0]:
                st.markdown(f"<h2 style='color:{sev_color};margin:0'>{i}</h2>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"**{f.title}**")
                st.caption(f"{f.description}")
            with cols[2]:
                st.markdown(f"<div style='text-align:right'><span style='background:{sev_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.8em'>{sev_label}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:right;margin-top:4px'><code>{f.category}</code> | Score: {f.score:.3f}</div>", unsafe_allow_html=True)

            with st.expander("🔍 Details"):
                det_cols = st.columns(3)
                with det_cols[0]:
                    st.markdown("**Severity**")
                    st.progress(f.severity)
                    st.caption(f"{f.severity:.2f}")
                with det_cols[1]:
                    st.markdown("**Specificity**")
                    st.progress(f.specificity)
                    st.caption(f"{f.specificity:.2f}")
                with det_cols[2]:
                    st.markdown("**Surprise**")
                    st.progress(f.surprise)
                    st.caption(f"{f.surprise:.2f}")

                st.markdown("**Affected Tables**")
                st.write(", ".join(f"`{t}`" for t in f.affected_tables))
                st.markdown("**Query**")
                st.code(f.query, language="sql")


# ═══════════════════════════════════════════════════════════════
#  JOB TIMEFRAME & PREDICTION QUERIES
# ═══════════════════════════════════════════════════════════════

TIMEFRAME_SQL = """
    SELECT
        j.Id, j.JobNumber, j.Description, j.JobState,
        j.PlannedStartDate, j.PlannedEndDate, j.OnHold, j.ControlledJob,
        c.Name AS Vendor, sa.StandardActivityNumber,
        DATEDIFF(DAY, j.PlannedStartDate, j.PlannedEndDate) AS PlannedDurationDays,
        MIN(rlrj.LockOnDate) AS ActualStart, MAX(rlrj.LockOffDate) AS ActualEnd,
        DATEDIFF(DAY, MIN(rlrj.LockOnDate), MAX(rlrj.LockOffDate)) AS ActualDurationDays,
        COUNT(DISTINCT rlrj.Id) AS LockEventCount,
        COUNT(DISTINCT rj.RFIId) AS RFICount
    FROM Jobs j
    INNER JOIN Companies c ON j.CompanyId = c.Id
    LEFT JOIN StandardActivities sa ON j.StandardActivityId = sa.Id
    LEFT JOIN RFIJobs rj ON rj.JobId = j.Id AND rj.DeletedDate IS NULL
    LEFT JOIN RFILocksRFIJobs rlrj ON rlrj.RFIJobId = rj.Id AND rlrj.DeletedDate IS NULL
    WHERE j.DeletedDate IS NULL
    GROUP BY j.Id, j.JobNumber, j.Description, j.JobState,
             j.PlannedStartDate, j.PlannedEndDate, j.OnHold,
             j.ControlledJob, c.Name, sa.StandardActivityNumber
"""

@st.cache_data(ttl=120, show_spinner=False)
def get_job_timeframe_data():
    """Return a DataFrame comparing planned vs actual durations per job."""
    rows = query(TIMEFRAME_SQL)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Compute derived columns
    df["HasActualDates"] = df["ActualStart"].notna() & df["ActualEnd"].notna()
    df["HasPlannedDates"] = df["PlannedStartDate"].notna() & df["PlannedEndDate"].notna()
    df["ScheduleVariance"] = df["ActualDurationDays"] - df["PlannedDurationDays"]
    df["OnTime"] = df.apply(
        lambda r: r["ActualDurationDays"] <= r["PlannedDurationDays"]
        if (pd.notna(r["ActualDurationDays"]) and pd.notna(r["PlannedDurationDays"]))
        else None, axis=1
    )
    return df


def get_prediction_dataset(df=None):
    """
    Build a training dataset: completed jobs (JobState=2) with actual durations.
    Accepts optional DataFrame to avoid re-querying.
    """
    if df is None:
        df = get_job_timeframe_data()
    if df.empty:
        return pd.DataFrame()
    completed = df[
        (df["JobState"] == 2) &
        (df["HasActualDates"]) &
        (df["HasPlannedDates"]) &
        (df["ActualDurationDays"] > 0) &
        (df["PlannedDurationDays"] > 0)
    ].copy()
    return completed


# ═══════════════════════════════════════════════════════════════
#  JOB TIMEFRAME & PREDICTION CHARTS
# ═══════════════════════════════════════════════════════════════

def chart_gantt_comparison(df, top_n=30):
    """Gantt chart comparing planned vs actual timelines for top N jobs by duration."""
    if df.empty:
        return None
    plot = df.head(top_n).copy()
    plot["JobLabel"] = plot["JobNumber"].str[:20] + ": " + plot["Description"].str[:30]
    fig = go.Figure()
    # Planned bars
    fig.add_trace(go.Bar(
        y=plot["JobLabel"],
        x=plot["PlannedDurationDays"],
        orientation="h",
        name="Planned Duration",
        marker_color="#3498db",
        opacity=0.7,
    ))
    # Actual bars
    fig.add_trace(go.Bar(
        y=plot["JobLabel"],
        x=plot["ActualDurationDays"],
        orientation="h",
        name="Actual Duration",
        marker_color="#e74c3c",
        opacity=0.7,
    ))
    fig.update_layout(
        title=f"Top {top_n} Jobs: Planned vs Actual Duration (days)",
        barmode="group",
        yaxis={"categoryorder": "total ascending", "autorange": "reversed"},
        xaxis_title="Duration (days)",
        height=max(400, top_n * 28),
    )
    return apply_theme(fig)


def chart_schedule_variance(df):
    """Histogram of schedule variance (actual - planned days). Negative = early, positive = late."""
    if df.empty:
        return None
    valid = df.dropna(subset=["ScheduleVariance"]).copy()
    valid = valid[valid["ScheduleVariance"].between(-200, 200)]
    if valid.empty:
        return None
    fig = px.histogram(
        valid, x="ScheduleVariance", nbins=50,
        title="Schedule Variance Distribution (Actual - Planned Days)",
        labels={"ScheduleVariance": "Days (negative = early, positive = late)"},
        color_discrete_sequence=["#f39c12"],
    )
    fig.add_vline(x=0, line_dash="dash", line_color="white", opacity=0.5)
    return apply_theme(fig)


def chart_vendor_performance(df):
    """Bar chart showing average schedule variance by vendor."""
    if df.empty:
        return None
    agg = df.dropna(subset=["ScheduleVariance"]).groupby("Vendor").agg(
        AvgVariance=("ScheduleVariance", "mean"),
        JobCount=("JobNumber", "count"),
    ).reset_index()
    agg = agg[agg["JobCount"] >= 3].sort_values("AvgVariance")
    if agg.empty:
        return None
    colors = ["#e74c3c" if v > 0 else "#2ecc71" for v in agg["AvgVariance"]]
    fig = go.Figure(go.Bar(
        x=agg["AvgVariance"],
        y=agg["Vendor"],
        orientation="h",
        marker_color=colors,
        text=agg["JobCount"].apply(lambda n: f"{n} jobs"),
        textposition="outside",
    ))
    fig.update_layout(
        title="Vendor Performance: Average Schedule Variance (days)",
        xaxis_title="Avg Days (negative = early, positive = late)",
        yaxis={"categoryorder": "total ascending", "autorange": "reversed"},
        height=max(300, len(agg) * 25),
    )
    fig.add_vline(x=0, line_dash="dash", line_color="white", opacity=0.5)
    return apply_theme(fig)


def chart_planned_vs_actual_scatter(df):
    """Scatter: planned duration vs actual duration. Diagonal = on-time."""
    if df.empty:
        return None
    valid = df.dropna(subset=["PlannedDurationDays", "ActualDurationDays"]).copy()
    valid = valid[
        (valid["PlannedDurationDays"] > 0) &
        (valid["ActualDurationDays"] > 0) &
        (valid["PlannedDurationDays"] <= 1000) &
        (valid["ActualDurationDays"] <= 1000)
    ]
    if valid.empty:
        return None
    max_d = max(valid["PlannedDurationDays"].max(), valid["ActualDurationDays"].max())
    fig = px.scatter(
        valid, x="PlannedDurationDays", y="ActualDurationDays",
        color="Vendor", hover_data=["JobNumber", "Description", "ScheduleVariance"],
        title="Planned vs Actual Duration (completed jobs)",
        labels={"PlannedDurationDays": "Planned (days)", "ActualDurationDays": "Actual (days)"},
        opacity=0.6,
    )
    # On-time diagonal
    fig.add_trace(go.Scatter(
        x=[0, max_d], y=[0, max_d],
        mode="lines", line=dict(dash="dash", color="white", width=1),
        name="On-time line", showlegend=True,
    ))
    fig.update_layout(height=500)
    return apply_theme(fig)


def chart_prediction_results(predictions, feature_importance):
    """Show predicted vs actual for validation set + upcoming job predictions."""
    if predictions.empty:
        return None, None
    # Scatter: predicted vs actual
    fig1 = px.scatter(
        predictions, x="ActualDurationDays", y="PredictedDurationDays",
        hover_data=["JobNumber"],
        title="Model Validation: Predicted vs Actual Duration (days)",
        labels={"ActualDurationDays": "Actual (days)", "PredictedDurationDays": "Predicted (days)"},
        opacity=0.5,
    )
    max_d = max(predictions["ActualDurationDays"].max(), predictions["PredictedDurationDays"].max())
    fig1.add_trace(go.Scatter(
        x=[0, max_d], y=[0, max_d],
        mode="lines", line=dict(dash="dash", color="white", width=1),
        name="Perfect prediction",
    ))
    fig1.update_layout(height=400)
    fig1 = apply_theme(fig1)

    # Feature importance
    if not feature_importance.empty:
        fi = feature_importance.sort_values("Importance", ascending=True)
        fig2 = go.Figure(go.Bar(
            x=fi["Importance"], y=fi["Feature"], orientation="h",
            marker_color="#2ecc71",
        ))
        fig2.update_layout(title="Feature Importance", xaxis_title="Importance", height=300)
        fig2 = apply_theme(fig2)
    else:
        fig2 = None

    return fig1, fig2


# ═══════════════════════════════════════════════════════════════
#  JOB TIMEFRAME & PREDICTION PAGE
# ═══════════════════════════════════════════════════════════════

def page_job_timeframes(flt):
    st.title("⏱️ Job Timeframes & Completion Prediction")
    st.caption("Compare planned vs actual durations and predict future job completions")

    sub_tab = st.radio("View", [
        "📊 Overview & Comparison",
        "📈 Detailed Analysis",
        "🔮 Predict Future Jobs",
    ], horizontal=True)

    with st.spinner("Loading job timeframe data…"):
        df = get_job_timeframe_data()

    if df.empty:
        st.warning("No job timeframe data available.")
        return

    # ---- KPI cards ----
    total_jobs = len(df)
    completed = df[df["JobState"] == 2]
    active = df[df["JobState"] == 1]
    cancelled = df[df["JobState"] == 0]
    completed_with_dates = completed.dropna(subset=["ScheduleVariance"])

    cols_kpi = st.columns(5)
    cols_kpi[0].metric("Total Jobs", f"{total_jobs:,}")
    cols_kpi[1].metric("Completed", f"{len(completed):,}")
    cols_kpi[2].metric("Active", f"{len(active):,}")
    cols_kpi[3].metric("Cancelled", f"{len(cancelled):,}")
    if not completed_with_dates.empty:
        on_time_pct = completed_with_dates["OnTime"].mean() * 100
        avg_variance = completed_with_dates["ScheduleVariance"].mean()
        cols_kpi[4].metric("On-Time Rate", f"{on_time_pct:.0f}%", f"{avg_variance:+.0f}d avg")

    # ================================================================
    # TAB 1: Overview & Comparison
    # ================================================================
    if sub_tab == "📊 Overview & Comparison":
        st.subheader("Planned vs Actual Duration")
        st.caption(f"Showing completed jobs ({len(completed_with_dates)}) with both planned and actual dates")

        # Filter controls
        c1, c2, c3 = st.columns(3)
        with c1:
            vendor_filter = st.selectbox(
                "Vendor",
                options=["All"] + sorted(df["Vendor"].dropna().unique().tolist()),
            )
        with c2:
            min_duration = st.number_input("Min Planned Duration (days)", 0, 500, 0)
        with c3:
            max_duration = st.number_input("Max Planned Duration (days)", 1, 3650, 500)

        plot_df = completed_with_dates.copy()
        if vendor_filter != "All":
            plot_df = plot_df[plot_df["Vendor"] == vendor_filter]
        plot_df = plot_df[
            (plot_df["PlannedDurationDays"] >= min_duration) &
            (plot_df["PlannedDurationDays"] <= max_duration)
        ]

        if not plot_df.empty:
            # Gantt comparison
            sort_by = st.selectbox("Sort by", ["PlannedDurationDays", "ActualDurationDays", "ScheduleVariance"], index=2)
            plot_df = plot_df.sort_values(sort_by, ascending=False)
            fig = chart_gantt_comparison(plot_df, 30)
            if fig:
                st.plotly_chart(fig, width='stretch')

            # Data table with key columns
            st.caption(f"{len(plot_df):,} jobs matching filters")
            display_cols = ["JobNumber", "Description", "Vendor", "JobState",
                            "PlannedStartDate", "PlannedEndDate", "ActualStart", "ActualEnd",
                            "PlannedDurationDays", "ActualDurationDays", "ScheduleVariance", "OnTime"]
            available = [c for c in display_cols if c in plot_df.columns]
            st.dataframe(plot_df[available], use_container_width=True, height=400)

            csv = plot_df[available].to_csv(index=False).encode()
            st.download_button("📥 Download CSV", csv, "job_timeframes.csv", "text/csv")
        else:
            st.info("No jobs match the current filters.")

    # ================================================================
    # TAB 2: Detailed Analysis
    # ================================================================
    elif sub_tab == "📈 Detailed Analysis":
        st.subheader("Schedule Variance Analysis")

        c1, c2 = st.columns(2)
        with c1:
            fig_var = chart_schedule_variance(completed_with_dates)
            if fig_var:
                st.plotly_chart(fig_var, width='stretch')
            else:
                st.info("Insufficient variance data.")
        with c2:
            fig_scatter = chart_planned_vs_actual_scatter(completed_with_dates)
            if fig_scatter:
                st.plotly_chart(fig_scatter, width='stretch')
            else:
                st.info("Insufficient scatter data.")

        st.subheader("Vendor Performance")
        fig_vendor = chart_vendor_performance(completed_with_dates)
        if fig_vendor:
            st.plotly_chart(fig_vendor, width='stretch')
        else:
            st.info("Insufficient vendor data (need ≥3 completed jobs per vendor).")

        st.subheader("Duration Statistics by Vendor")
        if not completed_with_dates.empty:
            stats = completed_with_dates.groupby("Vendor").agg(
                Jobs=("JobNumber", "count"),
                AvgPlanned=("PlannedDurationDays", "mean"),
                AvgActual=("ActualDurationDays", "mean"),
                AvgVariance=("ScheduleVariance", "mean"),
                MedianVariance=("ScheduleVariance", "median"),
                OnTimeRate=("OnTime", "mean"),
                AvgLockEvents=("LockEventCount", "mean"),
                AvgRFIs=("RFICount", "mean"),
            ).reset_index()
            stats["OnTimeRate"] = (stats["OnTimeRate"] * 100).round(0).astype(int)
            stats = stats[stats["Jobs"] >= 3].sort_values("AvgVariance")
            st.dataframe(stats, use_container_width=True, height=400)

    # ================================================================
    # TAB 3: Predict Future Jobs
    # ================================================================
    elif sub_tab == "🔮 Predict Future Jobs":
        st.subheader("Predict Completion Durations for Active/Cancelled Jobs")
        st.caption(
            "Uses historical completed-job patterns to estimate how long "
            "active or newly-created jobs will take. "
            "Model: historical average duration per vendor + actual lock-event rate."
        )

        # Get completed jobs for training (reuse the df we already loaded)
        training = get_prediction_dataset(df)
        if training.empty:
            st.warning("No completed jobs with both planned and actual dates found for training.")
            return

        st.write(f"**Training data:** {len(training):,} completed jobs with actual durations")

        # --- Simple but robust prediction model ---
        # Method: weighted blend of:
        #   1. Vendor historical average duration (weighted by job count)
        #   2. Planned duration (regression factor from historical planned→actual ratio)
        #   3. Complexity proxy: lock events per RFI ratio

        # Compute vendor-level stats
        vendor_stats = training.groupby("Vendor").agg(
            VendorAvgActual=("ActualDurationDays", "mean"),
            VendorAvgPlanned=("PlannedDurationDays", "mean"),
            VendorCount=("JobNumber", "count"),
        ).reset_index()
        vendor_stats["VendorRatio"] = vendor_stats["VendorAvgActual"] / vendor_stats["VendorAvgPlanned"].clip(lower=1)

        # Global ratio (planned→actual conversion factor)
        global_ratio = training["ActualDurationDays"].sum() / training["PlannedDurationDays"].clip(lower=1).sum()

        # Predict for active + cancelled jobs
        future_jobs = df[df["JobState"].isin([0, 1])].copy()
        if future_jobs.empty:
            st.info("No active or cancelled jobs to predict.")
            return

        # Merge vendor stats
        future_jobs = future_jobs.merge(vendor_stats[["Vendor", "VendorAvgActual", "VendorRatio", "VendorCount"]], on="Vendor", how="left")

        # Prediction formula (simple weighted model)
        def predict_row(r):
            predictions = []
            # Vendor-based prediction (if available)
            if pd.notna(r["VendorAvgActual"]) and r.get("VendorCount", 0) >= 3:
                predictions.append(("vendor_mean", r["VendorAvgActual"], 0.4))
            # Planned-duration regression
            if pd.notna(r["PlannedDurationDays"]) and r["PlannedDurationDays"] > 0:
                # Use vendor ratio if available, otherwise global ratio
                ratio = r["VendorRatio"] if pd.notna(r["VendorRatio"]) else global_ratio
                predictions.append(("planned_regression", r["PlannedDurationDays"] * ratio, 0.4))
            # Complexity proxy: if we have lock-activity started, use elapsed time + rate
            if pd.notna(r["ActualStart"]) and pd.notna(r["LockEventCount"]) and r["LockEventCount"] > 0:
                elapsed = (pd.Timestamp.utcnow() - r["ActualStart"]).days
                if r["RFICount"] > 0:
                    per_rfi = elapsed / r["RFICount"]
                    # Estimate remaining RFIs (assume similar to vendor average)
                    avg_rfi = 2.0  # default
                    if pd.notna(r.get("VendorAvgActual")):
                        avg_rfi = max(1, r.get("RFICount", 2))
                    remaining = max(0, (r.get("RFICount", 2) - 1)) * per_rfi
                    predictions.append(("activity_based", elapsed + remaining, 0.2))
            if not predictions:
                return None
            total_weight = sum(w for _, _, w in predictions)
            return sum(v * w for _, v, w in predictions) / total_weight

        future_jobs["PredictedDurationDays"] = future_jobs.apply(predict_row, axis=1)
        future_jobs["PredictedEndDate"] = future_jobs.apply(
            lambda r: r["ActualStart"] + pd.Timedelta(days=r["PredictedDurationDays"])
            if pd.notna(r["ActualStart"]) and pd.notna(r["PredictedDurationDays"])
            else (r["PlannedEndDate"] if pd.notna(r["PlannedEndDate"]) else None),
            axis=1,
        )

        # --- Show predictions ---
        pred_valid = future_jobs.dropna(subset=["PredictedDurationDays"]).copy()
        if pred_valid.empty:
            st.info("Could not generate predictions for current active jobs.")
            return

        st.write(f"**Predictions generated for:** {len(pred_valid):,} jobs")

        # Summary metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Jobs Predicted", f"{len(pred_valid):,}")
        c2.metric("Avg Predicted Duration", f"{pred_valid['PredictedDurationDays'].mean():.0f} days")
        overdue = pred_valid[
            (pred_valid["PlannedEndDate"].notna()) &
            (pred_valid["PredictedEndDate"] > pred_valid["PlannedEndDate"])
        ]
        c3.metric("Predicted Overdue", f"{len(overdue):,}", f"{len(overdue)/len(pred_valid)*100:.0f}%")

        # Table of predictions
        st.subheader("Upcoming Job Predictions")
        pred_display = pred_valid[[
            "JobNumber", "Description", "Vendor", "JobState", "OnHold",
            "PlannedStartDate", "PlannedEndDate", "ActualStart",
            "PredictedDurationDays", "PredictedEndDate", "RFICount", "LockEventCount"
        ]].sort_values("PredictedEndDate", ascending=True)
        pred_display["JobState"] = pred_display["JobState"].map({0: "Cancelled", 1: "Active"})
        st.dataframe(pred_display, use_container_width=True, height=500)

        csv2 = pred_display.to_csv(index=False).encode()
        st.download_button("📥 Download Predictions CSV", csv2, "job_predictions.csv", "text/csv")

        # Validation: how well does this predict on completed jobs?
        st.subheader("Model Validation (on completed jobs)")
        completed_train = training.copy()
        completed_train = completed_train.merge(
            vendor_stats[["Vendor", "VendorAvgActual", "VendorRatio", "VendorCount"]],
            on="Vendor", how="left"
        )
        completed_train["PredictedDurationDays"] = completed_train.apply(predict_row, axis=1)
        valid_completed = completed_train.dropna(subset=["PredictedDurationDays"])
        if not valid_completed.empty:
            valid_completed["Error"] = valid_completed["PredictedDurationDays"] - valid_completed["ActualDurationDays"]
            valid_completed["AbsError"] = valid_completed["Error"].abs()
            mae = valid_completed["AbsError"].mean()
            st.write(f"**MAE on completed jobs:** {mae:.1f} days (mean absolute error)")

            fig_pred, _ = chart_prediction_results(
                valid_completed[["ActualDurationDays", "PredictedDurationDays", "JobNumber"]],
                pd.DataFrame(),
            )
            if fig_pred:
                st.plotly_chart(fig_pred, width='stretch')

    # Show the SQL query
    show_sql(TIMEFRAME_SQL, "Job Timeframe Query")


GANTT_JOBS_SQL = """
    SELECT
        j.Id AS JobId, j.JobNumber, j.Description AS JobDescription,
        j.JobState, j.OnHold, j.ControlledJob,
        c.Name AS Vendor, sa.StandardActivityNumber,
        MIN(rlrj.LockOnDate) AS JobStart,
        MAX(rlrj.LockOffDate) AS JobEnd,
        DATEDIFF(DAY, MIN(rlrj.LockOnDate), MAX(rlrj.LockOffDate)) AS DurationDays,
        COUNT(DISTINCT rlrj.Id) AS LockEventCount,
        COUNT(DISTINCT rj.RFIId) AS RFICount
    FROM Jobs j
    INNER JOIN Companies c ON j.CompanyId = c.Id
    LEFT JOIN StandardActivities sa ON j.StandardActivityId = sa.Id
    LEFT JOIN RFIJobs rj ON rj.JobId = j.Id AND rj.DeletedDate IS NULL
    LEFT JOIN RFILocksRFIJobs rlrj ON rlrj.RFIJobId = rj.Id AND rlrj.DeletedDate IS NULL
    WHERE j.DeletedDate IS NULL
    GROUP BY j.Id, j.JobNumber, j.Description, j.JobState,
             j.OnHold, j.ControlledJob, c.Name, sa.StandardActivityNumber
    HAVING MIN(rlrj.LockOnDate) IS NOT NULL
        AND MAX(rlrj.LockOffDate) > '2000-01-01'
        AND MIN(rlrj.LockOnDate) <= MAX(rlrj.LockOffDate)
"""

GANTT_ISOLATIONS_SQL = """
    SELECT
        rj.JobId,
        j.JobNumber,
        r.RFINumber,
        i.Name AS IsolationPoint,
        ia.Name AS IsolationArea,
        e.Name AS Equipment,
        ri.AppliedDate AS IsoStart,
        ri.RemovalDate AS IsoEnd,
        ri.RFIIsolationState,
        CASE WHEN ri.RemovalDate IS NULL THEN 'Active' ELSE 'Removed' END AS IsoStatus
    FROM RFIIsolations ri
    INNER JOIN RFIs r ON ri.RFIId = r.Id AND r.DeletedDate IS NULL
    INNER JOIN IsolationPoints i ON ri.IsolationPointId = i.Id AND i.DeletedDate IS NULL
    INNER JOIN Areas ia ON i.AreaId = ia.Id
    LEFT JOIN Equipment e ON ri.EquipmentId = e.Id AND e.DeletedDate IS NULL
    INNER JOIN RFIJobs rj ON rj.RFIId = r.Id AND rj.DeletedDate IS NULL
    INNER JOIN Jobs j ON rj.JobId = j.Id AND j.DeletedDate IS NULL
    WHERE ri.DeletedDate IS NULL
        AND ri.AppliedDate IS NOT NULL
        AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
"""

@st.cache_data(ttl=120, show_spinner=False)
def get_gantt_jobs_data():
    """Return DataFrame with job timelines for Gantt chart."""
    rows = query(GANTT_JOBS_SQL)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["JobStart"] = pd.to_datetime(df["JobStart"], utc=True)
    df["JobEnd"] = pd.to_datetime(df["JobEnd"], utc=True)
    # Map JobState to label
    state_map = {0: "Cancelled", 1: "Active", 2: "Completed"}
    df["JobStateLabel"] = df["JobState"].map(state_map).fillna("Unknown")
    return df

@st.cache_data(ttl=120, show_spinner=False)
def get_gantt_isolations_data():
    """Return DataFrame with isolation timelines for Gantt chart."""
    rows = query(GANTT_ISOLATIONS_SQL)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["IsoStart"] = pd.to_datetime(df["IsoStart"], utc=True)
    df["IsoEnd"] = pd.to_datetime(df["IsoEnd"], utc=True)
    return df


# ═══════════════════════════════════════════════════════════════
#  GANTT CHART BUILDERS
# ═══════════════════════════════════════════════════════════════

# Color maps
JOB_STATE_COLORS = {
    "Completed": "#2ecc71",   # green
    "Active": "#3498db",      # blue
    "Cancelled": "#e74c3c",   # red
    "Unknown": "#95a5a6",     # grey
}

ISO_STATUS_COLORS = {
    "Active": "#e74c3c",      # red = still isolated
    "Removed": "#2ecc71",     # green = removed/complete
}


def chart_gantt_jobs(df, max_jobs=30, color_by="JobStateLabel"):
    """
    Gantt chart for jobs using px.timeline.
    Each job is a horizontal bar from JobStart to JobEnd.
    Color-coded by JobState (Completed/Active/Cancelled).
    X-axis auto-scales to the data range.
    """
    if df.empty:
        return None

    plot_df = df.sort_values("JobStart", ascending=False).head(max_jobs).copy()
    plot_df["Label"] = plot_df["JobNumber"].str[:15] + ": " + plot_df["JobDescription"].str[:35]

    fig = px.timeline(
        plot_df,
        x_start="JobStart",
        x_end="JobEnd",
        y="Label",
        color=color_by,
        color_discrete_map=JOB_STATE_COLORS,
        title=f"Job Timeline — Top {len(plot_df)} Jobs by Start Date",
        labels={"Label": "", "JobStateLabel": "Job State"},
        hover_data={
            "Vendor": True,
            "LockEventCount": True,
            "RFICount": True,
            "DurationDays": True,
            "JobStart": "|%Y-%m-%d %H:%M",
            "JobEnd": "|%Y-%m-%d %H:%M",
        },
    )
    fig.update_yaxes(autorange="reversed")

    # Auto-scale x-axis to the actual data range
    x_min = plot_df["JobStart"].min()
    x_max = plot_df["JobEnd"].max()
    padding = (x_max - x_min) * 0.05 if x_max > x_min else pd.Timedelta(days=1)
    fig.update_xaxes(range=[x_min - padding, x_max + padding])

    fig.update_layout(
        height=max(400, len(plot_df) * 28),
        xaxis_title="Timeline",
    )
    return apply_theme(fig)


def chart_gantt_isolations(df, max_isos=50):
    """
    Gantt chart for isolations using px.timeline.
    Each isolation is a horizontal bar from AppliedDate to RemovalDate.
    Color-coded by status (Active/Removed).
    X-axis auto-scales to the data range.
    """
    if df.empty:
        return None

    plot_df = df.sort_values("IsoStart", ascending=False).head(max_isos).copy()
    equip = plot_df["Equipment"].fillna("").str[:20]
    plot_df["Label"] = (
        plot_df["IsolationPoint"].str[:25] + " — " +
        equip + " (" +
        plot_df["JobNumber"].str[:10] + ")"
    )

    fig = px.timeline(
        plot_df,
        x_start="IsoStart",
        x_end="IsoEnd",
        y="Label",
        color="IsoStatus",
        color_discrete_map=ISO_STATUS_COLORS,
        title=f"Isolation Timeline — Applied to Removal (Top {len(plot_df)})",
        labels={"Label": "", "IsoStatus": "Status"},
        hover_data={
            "JobNumber": True,
            "RFINumber": True,
            "IsolationArea": True,
            "IsoStart": "|%Y-%m-%d %H:%M",
            "IsoEnd": "|%Y-%m-%d %H:%M",
        },
    )
    fig.update_yaxes(autorange="reversed")

    # Auto-scale x-axis to the actual data range
    x_min = plot_df["IsoStart"].min()
    x_max = plot_df["IsoEnd"].max()
    padding = (x_max - x_min) * 0.05 if x_max > x_min else pd.Timedelta(days=1)
    fig.update_xaxes(range=[x_min - padding, x_max + padding])

    fig.update_layout(
        height=max(400, len(plot_df) * 22),
        xaxis_title="Timeline",
    )
    return apply_theme(fig)


def chart_gantt_cross_section(records):
    """Render a cross-section Gantt from a pre-built records list.
    Each record: {Task, Start, End, Color, Detail}
    Relationship colors:
      Throughout (purple)  — isolation covers the job's *entire* duration
      Started earlier (orange) — isolation began before the job, ended during it
      Ends later (red)     — isolation began during the job, extends past it
      Fits within (green)  — isolation applied and removed inside the job window"""
    if not records:
        return None
    plot_df = pd.DataFrame(records)
    color_map = {"Job": "#3498db", "Fits within": "#2ecc71",
                 "Started earlier": "#e67e22", "Ends later": "#e74c3c",
                 "Throughout": "#9b59b6"}
    job_count = plot_df["Task"].str.contains("📋", na=False).sum()
    n_isos = len(plot_df) - job_count
    fig = px.timeline(plot_df, x_start="Start", x_end="End", y="Task",
                      color="Color", color_discrete_map=color_map,
                      title=f"Cross-section: {job_count} jobs, {n_isos} related isolations",
                      labels={"Task": "", "Color": "Relationship"},
                      hover_data={"Detail": True, "Start": "|%Y-%m-%d", "End": "|%Y-%m-%d"},
                      category_orders={"Color": ["Job", "Fits within", "Started earlier", "Ends later", "Throughout"]})
    fig.update_yaxes(autorange="reversed", categoryorder="array",
                     categoryarray=[r["Task"] for r in records])
    fig.update_layout(height=max(300, len(records) * 20))
    mn, mx = plot_df["Start"].min(), plot_df["End"].max()
    if pd.notna(mn) and pd.notna(mx) and mx > mn:
        fig.update_xaxes(range=[mn - (mx - mn) * 0.01, mx + (mx - mn) * 0.01])
    return apply_theme(fig)


# ═══════════════════════════════════════════════════════════════
#  GANTT PAGE
# ═══════════════════════════════════════════════════════════════

def page_gantt_jobs_isolations(flt):
    st.title("📊 Gantt Chart — Jobs & Isolations")
    st.caption("Search jobs, explore timelines, and view isolation periods")

    # ── Search & Filter Panel ──
    with st.expander("🔍 Search & Filters", expanded=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            search_job = st.text_input("Job Number / Description", placeholder="e.g. WO-SYD-00004869")
        with fcol2:
            filter_vendor = st.text_input("Vendor", placeholder="e.g. BHP")
        with fcol3:
            filter_state = st.multiselect(
                "Job State",
                options=["Completed", "Active", "Cancelled"],
                default=["Completed", "Active", "Cancelled"],
            )
        with fcol4:
            iso_status_filter = st.multiselect(
                "Isolation Status",
                options=["Active", "Removed"],
                default=["Active", "Removed"],
            )

        dcol1, dcol2 = st.columns(2)
        with dcol1:
            date_from = st.date_input("From", value=None, help="Filter jobs starting after this date")
        with dcol2:
            date_to = st.date_input("To", value=None, help="Filter jobs ending before this date")

    # ── Load Data ──
    col1, col2 = st.columns(2)
    with col1:
        with st.spinner("Loading jobs…"):
            jobs_df = get_gantt_jobs_data()
    with col2:
        with st.spinner("Loading isolations…"):
            iso_df = get_gantt_isolations_data()

    if jobs_df.empty:
        st.warning("No job timeline data found.")
        return

    # ── Apply Filters ──
    filtered_jobs = jobs_df.copy()

    if search_job:
        mask = (
            filtered_jobs["JobNumber"].str.contains(search_job, case=False, na=False) |
            filtered_jobs["JobDescription"].str.contains(search_job, case=False, na=False)
        )
        filtered_jobs = filtered_jobs[mask]

    if filter_vendor:
        filtered_jobs = filtered_jobs[filtered_jobs["Vendor"].str.contains(filter_vendor, case=False, na=False)]

    if filter_state:
        filtered_jobs = filtered_jobs[filtered_jobs["JobStateLabel"].isin(filter_state)]

    if date_from:
        filtered_jobs = filtered_jobs[filtered_jobs["JobStart"] >= pd.Timestamp(date_from, tz="UTC")]

    if date_to:
        filtered_jobs = filtered_jobs[filtered_jobs["JobEnd"] <= pd.Timestamp(date_to, tz="UTC")]

    # Filter isolations to match
    if not iso_df.empty and iso_status_filter:
        iso_df = iso_df[iso_df["IsoStatus"].isin(iso_status_filter)]

    # ── KPI Cards ──
    total_jobs = len(filtered_jobs)
    completed = len(filtered_jobs[filtered_jobs["JobState"] == 2])
    active = len(filtered_jobs[filtered_jobs["JobState"] == 1])
    cancelled = len(filtered_jobs[filtered_jobs["JobState"] == 0])
    total_isos = len(iso_df) if not iso_df.empty else 0
    active_isos = len(iso_df[iso_df["IsoStatus"] == "Active"]) if not iso_df.empty else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Jobs", f"{total_jobs:,}")
    c2.metric("Completed", f"{completed:,}")
    c3.metric("Active", f"{active:,}")
    c4.metric("Cancelled", f"{cancelled:,}")
    c5.metric("Isolations", f"{total_isos:,}")
    c6.metric("Active Isolations", f"{active_isos:,}")

    if total_jobs == 0:
        st.info("No jobs match your filters. Try broadening your search.")
        return

    # ── View Selector ──
    view = st.radio(
        "View",
        ["📋 Jobs Only", "🔒 Isolations Only", "🎯 Job + Related Isos"],
        horizontal=True,
    )

    if view == "📋 Jobs Only":
        max_jobs = st.slider("Max jobs to display", 1, 50, 25)
        fig = chart_gantt_jobs(filtered_jobs, max_jobs)
        if fig:
            st.plotly_chart(fig, width='stretch')

    elif view == "🔒 Isolations Only":
        max_isos = st.slider("Max isolations to display", 1, 100, 40)
        if iso_df.empty:
            st.info("No isolation data available.")
        else:
            fig = chart_gantt_isolations(iso_df, max_isos)
            if fig:
                st.plotly_chart(fig, width='stretch')

    elif view == "🎯 Job + Related Isos":
        st.caption(
            "Select one or more jobs to see their lock periods and all related isolations. "
            "Isolations are colored by their relationship to each job's timeline."
        )
        # Build a clean job picker
        picker_df = filtered_jobs[["JobNumber", "JobDescription", "Vendor", "JobStart",
                                    "JobEnd", "DurationDays", "JobStateLabel"]].copy()
        picker_df["Label"] = picker_df["JobNumber"] + ": " + picker_df["JobDescription"].str[:50]
        picker_df = picker_df.dropna(subset=["JobStart", "JobEnd"])
        if picker_df.empty:
            st.info("No jobs with valid lock dates to select.")
        else:
            picker_df = picker_df.sort_values("JobStart", ascending=False)
            selected_labels = st.multiselect(
                "Select jobs to compare",
                picker_df["Label"].tolist(),
                help="Each selected job shows as a blue bar with its related isolations below",
            )

            if selected_labels:
                all_records = []
                sentences = []
                for label in selected_labels:
                    job = picker_df[picker_df["Label"] == label].iloc[0]
                    js, je = job["JobStart"], job["JobEnd"]

                    # All isolations linked to this job via RFIJobs → RFIs → RFIIsolations
                    related = iso_df[
                        iso_df["JobNumber"] == job["JobNumber"]
                    ].copy()

                    # Classify & count relationships
                    rel_counts = {"Fits within": 0, "Started earlier": 0,
                                  "Ends later": 0, "Throughout": 0}

                    # Job bar
                    all_records.append({
                        "Task": f"📋 {job['JobNumber']}: {str(job['JobDescription'])[:45]}",
                        "Start": js, "End": je,
                        "Color": "Job",
                        "Detail": f"{job.get('Vendor','')}",
                    })

                    # Isolation bars
                    for _, iso in related.iterrows():
                        ie = iso["IsoEnd"] if pd.notna(iso["IsoEnd"]) else je
                        if iso["IsoStart"] <= ie:
                            if iso["IsoStart"] < js and (pd.isna(iso["IsoEnd"]) or iso["IsoEnd"] > je):
                                rel = "Throughout"
                            elif iso["IsoStart"] < js:
                                rel = "Started earlier"
                            elif pd.isna(iso["IsoEnd"]) or iso["IsoEnd"] > je:
                                rel = "Ends later"
                            else:
                                rel = "Fits within"
                            rel_counts[rel] += 1
                            equip = iso["Equipment"] if pd.notna(iso["Equipment"]) else ""
                            equip_str = f" ({equip})" if pd.notna(equip) and equip else ""
                            all_records.append({
                                "Task": f"  {iso['IsolationPoint']}{equip_str}",
                                "Start": iso["IsoStart"], "End": ie,
                                "Color": rel,
                                "Detail": f"{iso.get('IsolationArea','')} | {iso.get('RFINumber','')} | {rel}",
                            })

                    # Generate sentence
                    dur = int(job.get("DurationDays", 0) or 0)
                    state = job.get("JobStateLabel", "Unknown")
                    total_isos = sum(rel_counts.values())
                    bits = [f"**{job['JobNumber']}** — {str(job['JobDescription'])[:60]}"]
                    bits.append(f"Lasted **{dur} day{'s' if dur != 1 else ''}** ({state})")

                    if total_isos > 0:
                        detail = []
                        for rt in ["Fits within", "Started earlier", "Ends later", "Throughout"]:
                            if rel_counts[rt] > 0:
                                detail.append(f"{rel_counts[rt]} {rt.lower()}")
                        bits.append(f"{total_isos} related isolation{'s' if total_isos != 1 else ''}: {', '.join(detail)}")
                    else:
                        bits.append("No related isolations")

                    sentences.append(" — ".join(bits))

                # Display generated sentences
                for s in sentences:
                    st.markdown(f"• {s}")

                total_jobs_charted = sum(1 for r in all_records if r["Color"] == "Job")
                if total_jobs_charted > 0:
                    fig = chart_gantt_cross_section(all_records)
                    if fig:
                        st.plotly_chart(fig, width='stretch')
                else:
                    st.info("No data to display for the selected jobs.")

    # ── Data Tables ──
    tab1, tab2 = st.tabs(["📋 Jobs Data", "🔒 Isolations Data"])
    with tab1:
        display_cols = ["JobNumber", "JobDescription", "Vendor", "JobStateLabel",
                        "JobStart", "JobEnd", "DurationDays", "LockEventCount", "RFICount"]
        available = [c for c in display_cols if c in filtered_jobs.columns]
        st.dataframe(filtered_jobs[available], use_container_width=True, height=400)
        st.download_button("📥 Download Jobs CSV",
                           filtered_jobs[available].to_csv(index=False).encode(),
                           "gantt_jobs.csv", "text/csv")
    with tab2:
        if not iso_df.empty:
            iso_display = ["JobNumber", "RFINumber", "IsolationPoint", "Equipment",
                           "IsolationArea", "IsoStart", "IsoEnd", "IsoStatus"]
            avail = [c for c in iso_display if c in iso_df.columns]
            st.dataframe(iso_df[avail], use_container_width=True, height=400)
            st.download_button("📥 Download Isolations CSV",
                               iso_df[avail].to_csv(index=False).encode(),
                               "gantt_isolations.csv", "text/csv")
        else:
            st.info("No isolation data.")

    with st.expander("📝 SQL Queries", expanded=False):
        st.caption("Jobs Query")
        st.code(GANTT_JOBS_SQL, language="sql")
        st.caption("Isolations Query")
        st.code(GANTT_ISOLATIONS_SQL, language="sql")


# ═══════════════════════════════════════════════════════════════
#  CONSTRAINT ANALYZER — bottleneck gaps & concurrency
# ═══════════════════════════════════════════════════════════════

BOTTLENECK_SQL = """
    SELECT
        i.Id, i.Name AS IsolationPoint,
        ia.Name AS Area,
        COUNT(DISTINCT rj.JobId) AS JobCount,
        COUNT(DISTINCT ri.Id) AS IsolationCount,
        AVG(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS AvgDurationDays,
        MIN(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS MinDurationDays,
        MAX(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS MaxDurationDays,
        SUM(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS TotalDays
    FROM IsolationPoints i
    INNER JOIN Areas ia ON i.AreaId = ia.Id
    INNER JOIN RFIIsolations ri ON i.Id = ri.IsolationPointId AND ri.DeletedDate IS NULL
        AND ri.AppliedDate IS NOT NULL
        AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
    INNER JOIN RFIs r ON ri.RFIId = r.Id AND r.DeletedDate IS NULL
    INNER JOIN RFIJobs rj ON rj.RFIId = r.Id AND rj.DeletedDate IS NULL
    INNER JOIN Jobs j ON rj.JobId = j.Id AND j.DeletedDate IS NULL
    WHERE i.DeletedDate IS NULL
    GROUP BY i.Id, i.Name, ia.Name
    HAVING COUNT(DISTINCT rj.JobId) >= 2
"""

ISOLATION_GAP_SQL = """
    WITH IsoJobs AS (
        SELECT ri.AppliedDate AS IsoStart,
               COALESCE(ri.RemovalDate, GETUTCDATE()) AS IsoEnd,
               ri.IsolationPointId,
               j.JobNumber, j.Description AS JobDescription,
               r.RFINumber
        FROM RFIIsolations ri
        INNER JOIN RFIs r ON ri.RFIId = r.Id AND r.DeletedDate IS NULL
        INNER JOIN RFIJobs rj ON rj.RFIId = r.Id AND rj.DeletedDate IS NULL
        INNER JOIN Jobs j ON rj.JobId = j.Id AND j.DeletedDate IS NULL
        WHERE ri.DeletedDate IS NULL
          AND ri.AppliedDate IS NOT NULL
          AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
    )
    SELECT *,
           LAG(IsoEnd) OVER (PARTITION BY IsolationPointId ORDER BY IsoStart) AS PrevEnd,
           DATEDIFF(DAY, LAG(IsoEnd) OVER (PARTITION BY IsolationPointId ORDER BY IsoStart), IsoStart) AS GapDays
    FROM IsoJobs
"""

AREA_CONCURRENCY_SQL = """
    SELECT
        ia.Name AS Area,
        COUNT(DISTINCT i.Id) AS IsolationPoints,
        COUNT(DISTINCT ri.Id) AS IsolationEvents,
        COUNT(DISTINCT rj.JobId) AS JobsAffected,
        AVG(DATEDIFF(DAY, ri.AppliedDate, COALESCE(ri.RemovalDate, GETUTCDATE()))) AS AvgDurationDays
    FROM Areas ia
    INNER JOIN IsolationPoints i ON ia.Id = i.AreaId AND i.DeletedDate IS NULL
    INNER JOIN RFIIsolations ri ON i.Id = ri.IsolationPointId AND ri.DeletedDate IS NULL
        AND ri.AppliedDate IS NOT NULL
        AND (ri.RemovalDate IS NULL OR ri.RemovalDate > '2000-01-01')
    INNER JOIN RFIs r ON ri.RFIId = r.Id AND r.DeletedDate IS NULL
    INNER JOIN RFIJobs rj ON rj.RFIId = r.Id AND rj.DeletedDate IS NULL
    WHERE ia.DeletedDate IS NULL
    GROUP BY ia.Name
    ORDER BY JobsAffected DESC
"""


@st.cache_data(ttl=120, show_spinner=False)
def get_bottleneck_data():
    rows = query(BOTTLENECK_SQL)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def get_area_concurrency_data():
    rows = query(AREA_CONCURRENCY_SQL)
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_gap_timeline_for_point(point_id):
    """Uncached — filtered by isolation point. Returns jobs + gap calculations."""
    rows = query(
        ISOLATION_GAP_SQL + " AND ri.IsolationPointId = %(pid)s",
        {"pid": point_id},
    )
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    if not df.empty:
        df["IsoStart"] = pd.to_datetime(df["IsoStart"], utc=True)
        df["IsoEnd"] = pd.to_datetime(df["IsoEnd"], utc=True)
        df["GapDays"] = pd.to_numeric(df["GapDays"], errors="coerce")
    return df


# ═══════════════════════════════════════════════════════════════
#  CONSTRAINT ANALYZER CHARTS
# ═══════════════════════════════════════════════════════════════

def chart_bottleneck_bar(df, top_n=20):
    if df.empty:
        return None
    plot = df.head(top_n).copy()
    fig = px.bar(plot, x="JobCount", y="IsolationPoint",
                 color="AvgDurationDays", color_continuous_scale="Viridis",
                 orientation="h",
                 title=f"Top {top_n} Isolation Points by Job Count",
                 labels={"JobCount": "Distinct Jobs", "IsolationPoint": "",
                         "AvgDurationDays": "Avg Duration (d)"},
                 hover_data={"Area": True, "IsolationCount": True,
                             "AvgDurationDays": ":.0f", "MaxDurationDays": True})
    fig.update_yaxes(categoryorder="total ascending")
    return apply_theme(fig)


def chart_area_concurrency(df):
    if df.empty:
        return None
    fig = px.scatter(df, x="IsolationPoints", y="JobsAffected",
                     size="IsolationEvents", color="AvgDurationDays",
                     color_continuous_scale="Viridis",
                     hover_data={"Area": True, "IsolationEvents": True},
                     title="Area Overcrowding: Isolation Points vs Jobs Affected",
                     labels={"IsolationPoints": "Isolation Points in Area",
                             "JobsAffected": "Jobs Affected"})
    return apply_theme(fig)


def chart_gap_timeline(df):
    """Timeline of isolation uses on a single point, with gaps highlighted."""
    if df.empty:
        return None
    records = []
    for _, r in df.iterrows():
        gap = r.get("GapDays", 0)
        gap_label = f"Gap: {gap:.0f}d" if pd.notna(gap) and gap > 0 else ""
        records.append({
            "Task": f"{r['JobNumber']}: {str(r['JobDescription'])[:40]}",
            "Start": r["IsoStart"],
            "End": r["IsoEnd"],
            "Gap": gap_label,
        })
        if gap_label:
            prev_end = r.get("PrevEnd")
            if pd.notna(prev_end):
                records.append({
                    "Task": f"  ⬜ FREE: {gap:.0f}d gap",
                    "Start": prev_end,
                    "End": r["IsoStart"],
                    "Gap": gap_label,
                })
    if not records:
        return None
    plot_df = pd.DataFrame(records)
    plot_df["Color"] = plot_df["Gap"].apply(lambda g: "Gap" if g else "Job")
    color_map = {"Job": "#3498db", "Gap": "#2ecc71"}
    fig = px.timeline(plot_df, x_start="Start", x_end="End", y="Task",
                      color="Color", color_discrete_map=color_map,
                      title="Isolation Usage Timeline — jobs (blue) and free gaps (green)",
                      labels={"Task": "", "Color": ""},
                      hover_data={"Gap": True})
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=max(300, len(records) * 22), showlegend=False)
    mn, mx = plot_df["Start"].min(), plot_df["End"].max()
    if pd.notna(mn) and pd.notna(mx) and mx > mn:
        fig.update_xaxes(range=[mn - (mx - mn) * 0.02, mx + (mx - mn) * 0.02])
    return apply_theme(fig)


# ═══════════════════════════════════════════════════════════════
#  CONSTRAINT ANALYZER PAGE
# ═══════════════════════════════════════════════════════════════

def page_constraint_analyzer(flt):
    st.title("🔧 Constraint & Opportunity Analyzer")
    st.caption("Find scheduling gaps, bottleneck isolation points, and concurrency opportunities")

    tab_bottleneck, tab_gaps, tab_areas = st.tabs([
        "🔴 Bottleneck Points", "📅 Gap Timeline", "🗺️ Area Overcrowding"])

    # ── TAB 1: Bottleneck Points ──
    with tab_bottleneck:
        with st.spinner("Analyzing isolation point usage…"):
            df = get_bottleneck_data()
        if df.empty:
            st.warning("No bottleneck data available.")
        else:
            st.success(f"{len(df)} isolation points used by 2+ jobs")
            max_n = st.slider("Show top N", 10, min(100, len(df)), 25)
            fig = chart_bottleneck_bar(df, max_n)
            if fig:
                st.plotly_chart(fig, width='stretch')

            # Data table
            with st.expander("📋 All Bottleneck Points"):
                display = ["IsolationPoint", "Area", "JobCount", "IsolationCount",
                           "AvgDurationDays", "MinDurationDays", "MaxDurationDays", "TotalDays"]
                available = [c for c in display if c in df.columns]
                st.dataframe(df.sort_values("JobCount", ascending=False)[available],
                             use_container_width=True, height=400)
                csv = df[available].to_csv(index=False).encode()
                st.download_button("📥 Download CSV", csv, "bottlenecks.csv", "text/csv")

            with st.expander("📝 SQL Query"):
                st.code(BOTTLENECK_SQL, language="sql")

    # ── TAB 2: Gap Timeline ──
    with tab_gaps:
        with st.spinner("Loading isolation point list…"):
            pts = query("SELECT Id, Name FROM IsolationPoints WHERE DeletedDate IS NULL ORDER BY Name")
        if not pts:
            st.warning("No isolation points found.")
        else:
            pt_options = {p["Name"]: p["Id"] for p in pts}
            selected_pt = st.selectbox("Select an isolation point", list(pt_options.keys()))
            point_id = pt_options[selected_pt]

            with st.spinner(f"Loading timeline for {selected_pt}…"):
                gap_df = get_gap_timeline_for_point(point_id)

            if gap_df.empty:
                st.info("No isolation events for this point.")
            else:
                # Stats
                gaps = gap_df.dropna(subset=["GapDays"])
                total_jobs = gap_df["JobNumber"].nunique()
                total_events = len(gap_df)
                avg_gap = gaps["GapDays"].mean() if not gaps.empty else 0
                max_gap = gaps["GapDays"].max() if not gaps.empty else 0
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Jobs", total_jobs)
                c2.metric("Isolation Events", total_events)
                c3.metric("Avg Gap", f"{avg_gap:.0f}d" if avg_gap else "—")
                c4.metric("Max Gap", f"{max_gap:.0f}d" if max_gap else "—")

                fig = chart_gap_timeline(gap_df)
                if fig:
                    st.plotly_chart(fig, width='stretch')

                with st.expander("📋 Event Timeline Data"):
                    cols = ["JobNumber", "JobDescription", "RFINumber",
                            "IsoStart", "IsoEnd", "PrevEnd", "GapDays"]
                    avail = [c for c in cols if c in gap_df.columns]
                    st.dataframe(gap_df.sort_values("IsoStart")[avail],
                                 use_container_width=True, height=400)

    # ── TAB 3: Area Overcrowding ──
    with tab_areas:
        with st.spinner("Analyzing area-level concurrency…"):
            area_df = get_area_concurrency_data()
        if area_df.empty:
            st.warning("No area data available.")
        else:
            fig = chart_area_concurrency(area_df)
            if fig:
                st.plotly_chart(fig, width='stretch')

            with st.expander("📋 Area Data"):
                st.dataframe(area_df, use_container_width=True, height=400)
                csv = area_df.to_csv(index=False).encode()
                st.download_button("📥 Download CSV", csv, "areas.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════

st.set_page_config(page_title="OneTag HMAS Sydney — DB Explorer", page_icon="🏭", layout="wide", initial_sidebar_state="expanded")

# -- Sidebar --
st.sidebar.title("🏭 OneTag HMAS")
st.sidebar.caption("Lockout/Tagout DB Explorer")

ok, ver = check_connection()
if ok:
    st.sidebar.success(f"✅ Connected to SQL Server | {ver}")
else:
    st.sidebar.warning("⚠️ SQL Server unavailable — most data pages require it.")
    st.sidebar.info("The 🚀 Forrest Findings page works with local SQLite data regardless.")

page = st.sidebar.radio("Report", ["📊 Dashboard", "📋 RFI → Jobs → Vendors", "🔗 Jobs → Isolations → Equipment", "🔒 Lock History", "📜 RFI Log Timeline", "📊 Gantt Chart", "⏱️ Job Timeframes", "🔧 Constraints", "📈 Analysis", "🚀 Forrest Findings"])

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
    "📊 Gantt Chart": page_gantt_jobs_isolations,
    "⏱️ Job Timeframes": page_job_timeframes,
    "🔧 Constraints": page_constraint_analyzer,
    "📈 Analysis": page_analysis,
    "🚀 Forrest Findings": page_findings,
}

# -- Reconnect button --
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reconnect DB"):
    st.cache_data.clear()
    st.rerun()

# -- Error boundary --
try:
    pages[page](Filters)
except Exception as e:
    st.error(f"⚠️ Page error: {e}")
    st.info("Try clicking '🔄 Reconnect DB' in the sidebar, or refresh the page.")
    if st.button("Clear Cache & Retry"):
        st.cache_data.clear()
        st.rerun()
