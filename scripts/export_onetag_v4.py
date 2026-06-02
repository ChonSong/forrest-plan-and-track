#!/usr/bin/env python3
"""
OneTag HMAS Sydney — SQL Server to SQLite Export Tool (v4)
"""

import sqlite3
import subprocess
import sys
from pathlib import Path

SSH_KEY = "/home/hermeswebui/.ssh/id_ed25519"
SSH_HOST = "root@172.17.0.1"
CONTAINER = "sqlserver-onetag"
LOCAL_DB = Path("/workspace/forrest-plan-and-track/data/onetag.db")

def run_sql(sql, timeout=300):
    """Run SQL and return raw output."""
    escaped = sql.replace("'", "''").replace("\n", " ")
    cmd = f"""ssh -i {SSH_KEY} {SSH_HOST} "docker exec -u root {CONTAINER} /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P OneTagRestore2024! -N -C -W -s ',' -Q \\"{escaped}\\"" 2>&1"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout

def parse_output(output):
    """Parse sqlcmd CSV output into (headers, rows)."""
    lines = output.split('\n')
    
    # Skip "Changed database context" lines
    data_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('Changed database context'):
            continue
        if stripped.startswith('(') and 'rows affected' in stripped:
            continue
        if stripped:
            data_lines.append(stripped)
    
    if len(data_lines) < 2:
        return [], []
    
    # Line 0 = headers, line 1 = separator (dashes), line 2+ = data
    headers = [h.strip() for h in data_lines[0].split(',')]
    
    rows = []
    for line in data_lines[2:]:  # Skip header and separator
        values = line.split(',')
        row = {}
        for i, h in enumerate(headers):
            row[h] = values[i].strip() if i < len(values) else None
        rows.append(row)
    
    return headers, rows

def create_sqlite_db():
    LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL_DB.exists():
        LOCAL_DB.unlink()
    conn = sqlite3.connect(str(LOCAL_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.commit()
    conn.close()

def export_table(table_name, conn, limit=None):
    sql = f"SELECT * FROM [{table_name}]"
    if limit:
        sql = f"SELECT TOP {limit} * FROM [{table_name}]"
    
    output = run_sql(sql)
    headers, rows = parse_output(output)
    
    if not headers:
        print(f"  EMPTY: {table_name}")
        return 0
    
    c = conn.cursor()
    col_defs = ", ".join([f'"{h}" TEXT' for h in headers])
    c.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    c.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
    
    placeholders = ", ".join(["?"] * len(headers))
    insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
    
    count = 0
    for row in rows:
        values = [row.get(h, None) for h in headers]
        try:
            c.execute(insert_sql, values)
            count += 1
        except:
            pass
    
    conn.commit()
    size = f"({len(headers)} cols)" if count > 0 else ""
    print(f"  {table_name}: {count:,} rows {size}")
    return count

def main():
    print("OneTag HMAS — SQL Server → SQLite Export v4")
    print("=" * 50)
    
    # Check connectivity
    output = run_sql("SELECT 1 AS x")
    if '1' not in output:
        print("ERROR: SQL Server not responding")
        sys.exit(1)
    print("SQL Server: OK\n")
    
    # Create DB
    create_sqlite_db()
    conn = sqlite3.connect(str(LOCAL_DB))
    
    # Get tables with data
    output = run_sql("""
        USE [OneTag_Sydney];
        SELECT t.name, p.rows 
        FROM sys.tables t 
        JOIN sys.partitions p ON t.object_id = p.object_id 
        WHERE t.is_ms_shipped = 0 AND p.index_id IN (0,1) AND p.rows > 0
        ORDER BY p.rows DESC
    """)
    _, table_list = parse_output(output)
    print(f"Found {len(table_list)} tables with data\n")
    
    total_rows = 0
    total_tables = 0
    
    for t in table_list:
        name = t.get('name', '')
        rows = int(t.get('rows', 0) or 0)
        if not name or rows == 0:
            continue
        
        limit = 50000 if rows > 50000 else None
        count = export_table(name, conn, limit)
        total_rows += count
        total_tables += 1
    
    conn.close()
    
    db_size = LOCAL_DB.stat().st_size / (1024*1024)
    print(f"\n{'='*50}")
    print(f"Export complete!")
    print(f"  Tables exported: {total_tables}")
    print(f"  Total rows: {total_rows:,}")
    print(f"  Database: {LOCAL_DB}")
    print(f"  Size: {db_size:.1f} MB")

if __name__ == "__main__":
    main()
