#!/usr/bin/env python3
"""
OneTag HMAS — Web-based SQL Studio for SQL Server
Connects directly to SQL Server, no desktop environment needed.
"""

import sqlite3
import subprocess
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import html
import os
import sys

SSH_KEY = "/home/hermeswebui/.ssh/id_ed25519"
SSH_HOST = "root@172.17.0.1"
CONTAINER = "sqlserver-onetag"
PORT = 8766
SQL_SERVER = "localhost"
SQL_USER = "SA"
SQL_PASS = "OneTagRestore2024!"

def run_sql(sql, timeout=60):
    """Run SQL on SQL Server via SSH."""
    escaped = sql.replace("\\", "\\\\").replace("'", "''").replace("\n", " ")
    cmd = f"""ssh -i {SSH_KEY} -o ConnectTimeout=10 {SSH_HOST} "docker exec -u root {CONTAINER} /opt/mssql-tools18/bin/sqlcmd -S {SQL_SERVER} -U {SQL_USER} -P {SQL_PASS} -N -C -W -s ',' -Q \\"{escaped}\\"" 2>&1"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout, result.returncode

def parse_output(output):
    """Parse sqlcmd CSV output."""
    lines = output.split('\n')
    data_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('Changed database context'):
            continue
        if stripped.startswith('(') and 'rows affected' in stripped:
            continue
        if stripped.startswith('Msg '):
            raise Exception(stripped)
        data_lines.append(stripped)
    
    if len(data_lines) < 3:
        return [], []
    
    headers = [h.strip() for h in data_lines[0].split(',')]
    rows = []
    for line in data_lines[2:]:
        values = line.split(',')
        row = {}
        for i, h in enumerate(headers):
            row[h] = values[i].strip() if i < len(values) else None
        rows.append(row)
    return headers, rows

def get_tables():
    """Get list of tables with metadata."""
    output, rc = run_sql("""
        USE [OneTag_Sydney];
        SELECT 
            t.name AS table_name,
            SCHEMA_NAME(t.schema_id) AS schema_name,
            p.rows AS row_count,
            COUNT(c.column_id) AS column_count
        FROM sys.tables t
        JOIN sys.partitions p ON t.object_id = p.object_id
        JOIN sys.columns c ON t.object_id = c.object_id
        WHERE t.is_ms_shipped = 0 AND p.index_id IN (0,1) AND p.rows > 0
        GROUP BY t.name, t.schema_id, p.rows
        ORDER BY p.rows DESC
    """)
    if rc != 0:
        return []
    headers, rows = parse_output(output)
    return rows

def get_table_schema(table_name):
    """Get column definitions for a table."""
    output, rc = run_sql(f"""
        USE [OneTag_Sydney];
        SELECT 
            c.name AS column_name,
            ty.name AS data_type,
            c.max_length,
            c.is_nullable,
            CASE WHEN pk.column_id IS NOT NULL THEN 'PK' ELSE '' END AS is_pk,
            CASE WHEN fk.parent_column_id IS NOT NULL THEN 'FK' ELSE '' END AS is_fk,
            dc.definition AS default_value
        FROM sys.columns c
        JOIN sys.types ty ON c.user_type_id = ty.user_type_id
        LEFT JOIN (
            SELECT ic.object_id, ic.column_id
            FROM sys.index_columns ic
            JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
            WHERE i.is_primary_key = 1
        ) pk ON c.object_id = pk.object_id AND c.column_id = pk.column_id
        LEFT JOIN sys.foreign_key_columns fk ON c.object_id = fk.parent_object_id AND c.column_id = fk.parent_column_id
        LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
        WHERE c.object_id = OBJECT_ID(N'{table_name}')
        ORDER BY c.column_id
    """)
    if rc != 0:
        return []
    headers, rows = parse_output(output)
    return rows

def get_foreign_keys():
    """Get all foreign key relationships."""
    output, rc = run_sql("""
        USE [OneTag_Sydney];
        SELECT 
            fk.name AS constraint_name,
            OBJECT_NAME(fk.parent_object_id) AS from_table,
            COL_NAME(fk.parent_object_id, fkc.parent_column_id) AS from_column,
            OBJECT_NAME(fk.referenced_object_id) AS to_table,
            COL_NAME(fk.referenced_object_id, fkc.referenced_column_id) AS to_column
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        ORDER BY from_table, to_table
    """)
    if rc != 0:
        return []
    headers, rows = parse_output(output)
    return rows

def execute_query(sql):
    """Execute a custom SQL query."""
    output, rc = run_sql(sql)
    if rc != 0:
        return [], output
    try:
        headers, rows = parse_output(output)
        return rows, None
    except Exception as e:
        return [], str(e)

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        
        if path == "/":
            self.serve_index()
        elif path == "/api/tables":
            self.serve_json(get_tables())
        elif path == "/api/schema":
            table = params.get("table", [""])[0]
            self.serve_json(get_table_schema(table))
        elif path == "/api/fks":
            self.serve_json(get_foreign_keys())
        elif path == "/api/query":
            sql = urllib.parse.unquote(params.get("sql", [""])[0])
            rows, error = execute_query(sql)
            self.serve_json({"rows": rows, "error": error, "count": len(rows)})
        elif path == "/table":
            table_name = params.get("name", [""])[0]
            self.serve_table(table_name)
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def serve_index(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGE_HTML.encode())

    def serve_table(self, table_name):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        # Redirect to main page with table parameter
        self.wfile.write(f'<script>window.location="/?table={urllib.parse.quote(table_name)}"</script>'.encode())

    def log_message(self, format, *args):
        pass

PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OneTag HMAS — SQL Studio</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'SF Mono','Fira Code',monospace;background:#0d1117;color:#c9d1d9;display:flex;height:100vh;overflow:hidden}
#sidebar{width:320px;background:#161b22;border-right:1px solid #30363d;display:flex;flex-direction:column;overflow:hidden}
#sidebar h2{padding:0.8rem;color:#58a6ff;font-size:0.9rem;border-bottom:1px solid #30363d}
#search{padding:0.5rem;border-bottom:1px solid #30363d}
#search input{width:100%;background:#0d1117;border:1px solid #30363d;color:#c9d1d9;padding:0.4rem;border-radius:4px;font-size:0.75rem}
#search input:focus{outline:none;border-color:#58a6ff}
#table-list{flex:1;overflow-y:auto}
.table-item{padding:0.5rem 0.8rem;cursor:pointer;border-bottom:1px solid #21262d;font-size:0.75rem;display:flex;justify-content:space-between;align-items:center}
.table-item:hover{background:#1c2128}
.table-item.active{background:#1a3a5c}
.table-name{color:#e6edf3}
.table-meta{color:#6e7681;font-size:0.65rem}
#main{flex:1;display:flex;flex-direction:column;overflow:hidden}
#toolbar{padding:0.5rem;background:#161b22;border-bottom:1px solid #30363d;display:flex;gap:0.5rem;align-items:center}
#toolbar button{background:#238636;color:#fff;border:none;padding:0.4rem 0.8rem;border-radius:4px;cursor:pointer;font-size:0.75rem}
#toolbar button:hover{background:#2ea043}
#toolbar button.secondary{background:#30363d}
#sql-editor{flex:0 0 150px;background:#0d1117;border-bottom:1px solid #30363d;display:flex;flex-direction:column}
#sql-editor textarea{flex:1;background:transparent;color:#c9d1d9;border:none;padding:0.5rem;font-size:0.8rem;resize:none;font-family:inherit}
#sql-editor textarea:focus{outline:none}
#results{flex:1;overflow:auto;padding:0.5rem}
.results-table{width:100%;border-collapse:collapse;font-size:0.7rem}
.results-table th{background:#161b22;color:#58a6ff;padding:0.4rem;text-align:left;border-bottom:2px solid #30363d;position:sticky;top:0;white-space:nowrap}
.results-table td{padding:0.3rem 0.4rem;border-bottom:1px solid #21262d;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.results-table tr:hover td{background:#1c2128}
.error{color:#f85149;padding:1rem}
.schema-table{width:100%;border-collapse:collapse;font-size:0.7rem;margin-bottom:0.5rem}
.schema-table th{background:#161b22;color:#58a6ff;padding:0.3rem;text-align:left;font-size:0.65rem}
.schema-table td{padding:0.2rem 0.3rem;border-bottom:1px solid #21262d;font-size:0.65rem}
.pk{color:#f0883e;font-weight:bold}
.fk{color:#58a6ff}
.tabs{display:flex;border-bottom:1px solid #30363d}
.tab{padding:0.4rem 0.8rem;cursor:pointer;font-size:0.75rem;color:#8b949e}
.tab.active{color:#58a6ff;border-bottom:2px solid #58a6ff}
.fk-rel{font-size:0.65rem;color:#8b949e;margin:0.2rem 0;padding:0.2rem 0.4rem;background:#161b22;border-radius:4px}
.fk-arrow{color:#3fb950}
</style>
</head>
<body>
<div id="sidebar">
<h2>📋 Tables (<span id="table-count">0</span>)</h2>
<div id="search"><input type="text" id="table-search" placeholder="Search tables..." oninput="filterTables()"></div>
<div id="table-list"></div>
</div>
<div id="main">
<div id="toolbar">
<button onclick="runQuery()">▶ Run</button>
<button class="secondary" onclick="document.getElementById('sql').value=''">Clear</button>
<button class="secondary" onclick="showAllTables()">Show All Tables</button>
<button class="secondary" onclick="showRelationships()">Relationships</button>
<span style="flex:1"></span>
<span id="status" style="font-size:0.7rem;color:#6e7681"></span>
</div>
<div id="sql-editor">
<textarea id="sql" placeholder="Enter SQL query here...&#10;Example: SELECT TOP 100 * FROM Users">SELECT TOP 100 * FROM Users</textarea>
</div>
<div id="results"></div>
</div>

<script>
let tables = [];
let currentTable = null;

async function loadTables() {
    const resp = await fetch('/api/tables');
    tables = await resp.json();
    document.getElementById('table-count').textContent = tables.length;
    renderTables(tables);
}

function renderTables(list) {
    const el = document.getElementById('table-list');
    el.innerHTML = list.map(t => 
        `<div class="table-item" onclick="selectTable('${t.table_name}')">
            <span class="table-name">${t.table_name}</span>
            <span class="table-meta">${parseInt(t.row_count).toLocaleString()} rows</span>
        </div>`
    ).join('');
}

function filterTables() {
    const q = document.getElementById('table-search').value.toLowerCase();
    renderTables(tables.filter(t => t.table_name.toLowerCase().includes(q)));
}

async function selectTable(name) {
    currentTable = name;
    document.querySelectorAll('.table-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // Load schema
    const schemaResp = await fetch(`/api/schema?table=${encodeURIComponent(name)}`);
    const schema = await schemaResp.json();
    
    // Load data
    const dataResp = await fetch(`/api/query?sql=${encodeURIComponent('SELECT TOP 100 * FROM [' + name + ']')}`);
    const data = await dataResp.json();
    
    // Render
    let html = '<div class="tabs"><div class="tab active" onclick="showTab(this,\\'data\\')">Data (' + data.count + ')</div><div class="tab" onclick="showTab(this,\\'schema\\')">Schema (' + schema.length + ' cols)</div></div>';
    html += '<div id="tab-data">';
    if (data.error) html += '<div class="error">' + data.error + '</div>';
    else html += renderResults(data.rows);
    html += '</div>';
    html += '<div id="tab-schema" style="display:none">';
    html += '<table class="schema-table"><tr><th>Column</th><th>Type</th><th>Nullable</th><th>Key</th></tr>';
    schema.forEach(col => {
        const keyClass = col.is_pk === 'PK' ? 'pk' : (col.is_fk === 'FK' ? 'fk' : '');
        const key = col.is_pk === 'PK' ? '🔑 PK' : (col.is_fk === 'FK' ? '🔗 FK' : '');
        html += '<tr><td>' + col.column_name + '</td><td>' + col.data_type + '</td><td>' + (col.is_nullable == 1 ? 'YES' : 'NO') + '</td><td class="' + keyClass + '">' + key + '</td></tr>';
    });
    html += '</table></div>';
    
    document.getElementById('results').innerHTML = html;
    document.getElementById('sql').value = 'SELECT TOP 1000 * FROM [' + name + ']';
}

function renderResults(rows) {
    if (!rows || rows.length === 0) return '<div style="padding:1rem;color:#6e7681">No results</div>';
    const headers = Object.keys(rows[0]);
    let html = '<table class="results-table"><tr>' + headers.map(h => '<th>' + h + '</th>').join('') + '</tr>';
    rows.forEach(row => {
        html += '<tr>' + headers.map(h => '<td>' + (row[h] !== null ? row[h] : '<em style="color:#6e7681">null</em>') + '</td>').join('') + '</tr>';
    });
    html += '</table>';
    return html;
}

function showTab(el, tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tab-data').style.display = tab === 'data' ? '' : 'none';
    document.getElementById('tab-schema').style.display = tab === 'schema' ? '' : 'none';
}

async function runQuery() {
    const sql = document.getElementById('sql').value;
    const status = document.getElementById('status');
    status.textContent = 'Running...';
    try {
        const resp = await fetch('/api/query?sql=' + encodeURIComponent(sql));
        const data = await resp.json();
        if (data.error) {
            document.getElementById('results').innerHTML = '<div class="error">' + data.error + '</div>';
            status.textContent = 'Error';
        } else {
            document.getElementById('results').innerHTML = '<div style="padding:0.5rem;font-size:0.75rem;color:#3fb950">' + data.count + ' rows returned</div>' + renderResults(data.rows);
            status.textContent = data.count + ' rows';
        }
    } catch(e) {
        status.textContent = 'Failed';
    }
}

async function showAllTables() {
    const sql = "SELECT t.name, SCHEMA_NAME(t.schema_id) as schema_name, p.rows, COUNT(c.column_id) as columns FROM sys.tables t JOIN sys.partitions p ON t.object_id = p.object_id JOIN sys.columns c ON t.object_id = c.object_id WHERE t.is_ms_shipped = 0 AND p.index_id IN (0,1) AND p.rows > 0 GROUP BY t.name, t.schema_id, p.rows ORDER BY p.rows DESC";
    document.getElementById('sql').value = sql;
    runQuery();
}

async function showRelationships() {
    document.getElementById('results').innerHTML = '<div style="padding:1rem;color:#6e7681">Loading relationships...</div>';
    const resp = await fetch('/api/fks');
    const fks = await resp.json();
    let html = '<div style="padding:0.5rem;font-size:0.75rem;color:#3fb950">' + fks.length + ' foreign key relationships</div>';
    fks.forEach(fk => {
        html += '<div class="fk-rel"><strong>' + fk.from_table + '.' + fk.from_column + '</strong> <span class="fk-arrow">→</span> <strong>' + fk.to_table + '.' + fk.to_column + '</strong></div>';
    });
    document.getElementById('results').innerHTML = html;
}

// Keyboard shortcut
document.getElementById('sql').addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') runQuery();
});

// Auto-load from URL
const urlParams = new URLSearchParams(window.location.search);
const urlTable = urlParams.get('table');
loadTables().then(() => {
    if (urlTable) {
        const el = document.querySelector(`.table-item[onclick*="${urlTable}"]`);
        if (el) el.click();
    }
});
</script>
</body>
</html>"""

if __name__ == "__main__":
    print(f"OneTag HMAS — SQL Studio")
    print(f"  URL: http://localhost:{PORT}")
    print(f"  Connecting to SQL Server on host...")
    
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"  Server ready!")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
