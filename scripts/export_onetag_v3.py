#!/usr/bin/env python3
"""
OneTag HMAS Sydney — SQL Server to SQLite Export Tool (v3)
Handles sqlcmd CSV format with separator line.
"""

import sqlite3
import csv
import io
import subprocess
import sys
from pathlib import Path

SSH_KEY = "/home/hermeswebui/.ssh/id_ed25519"
SSH_HOST = "root@172.17.0.1"
CONTAINER = "sqlserver-onetag"
LOCAL_DB = Path("/workspace/forrest-plan-and-track/data/onetag.db")

def run_sql_csv(sql, timeout=300):
    """Run SQL and return output."""
    escaped = sql.replace("'", "''").replace("\n", " ")
    cmd = f"""ssh -i {SSH_KEY} {SSH_HOST} "docker exec -u root {CONTAINER} /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P OneTagRestore2024! -N -C -W -s ',' -Q \\"{escaped}\\"" 2>&1"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout, result.returncode

def parse_sqlcmd_csv(output):
    """Parse sqlcmd CSV output, skipping the separator line."""
    lines = [l for l in output.split('\n') if l.strip()]
    if not lines:
        return [], []
    
    # Find the header line (first line that looks like column names)
    # Skip "Changed database context" messages
    header_idx = None
    for i, line in enumerate(lines):
        if ',' in line and not line.startswith('Changed') and not line.startswith('('):
            # Check if next line is the separator (dashes)
            if i + 1 < len(lines) and lines[i+1].strip().startswith('--'):
                header_idx = i
                break
    
    if header_idx is None:
        return [], []
    
    headers = [h.strip() for h in lines[header_idx].split(',')]
    
    # Data starts after header + separator
    data_start = header_idx + 2
    data_rows = []
    
    for line in lines[data_start:]:
        if line.strip().startswith('(') and 'rows affected' in line:
            break
        if not line.strip():
            continue
        values = line.split(',')
        if len(values) >= len(headers):
            row = {}
            for i, h in enumerate(headers):
                row[h] = values[i].strip() if i < len(values) else None
            data_rows.append(row)
    
    return headers, data_rows

def create_sqlite_db():
    LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL_DB.exists():
        LOCAL_DB.unlink()
    conn = sqlite3.connect(str(LOCAL_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.commit()
    conn.close()

def export_table(table_name, conn, limit=None):
    sql = f"SELECT * FROM [{table_name}]"
    if limit:
        sql = f"SELECT TOP {limit} * FROM [{table_name}]"
    
    output, rc = run_sql_csv(sql)
    if rc != 0:
        print(f"  FAIL: {table_name}")
        return 0
    
    headers, rows = parse_sqlcmd_csv(output)
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
    print(f"  {table_name}: {count} rows, {len(headers)} cols")
    return count

def main():
    print("OneTag HMAS Sydney — SQL Server → SQLite Export v3")
    print("=" * 50)
    
    # Check connectivity
    output, rc = run_sql_csv("SELECT 1 AS x")
    if rc != 0:
        print("ERROR: SQL Server not responding")
        sys.exit(1)
    print("SQL Server: OK\n")
    
    # Create DB
    create_sqlite_db()
    conn = sqlite3.connect(str(LOCAL_DB))
    
    # Get tables with data
    output, rc = run_sql_csv("""
        USE [OneTag_Sydney];
        SELECT t.name, p.rows 
        FROM sys.tables t 
        JOIN sys.partitions p ON t.object_id = p.object_id 
        WHERE t.is_ms_shipped = 0 AND p.index_id IN (0,1) AND p.rows > 0
        ORDER BY p.rows DESC
    """)
    _, table_list = parse_sqlcmd_csv(output)
    print(f"Found {len(table_list)} tables with data\n")
    
    total_rows = 0
    total_tables = 0
    
    for t in table_list:
        name = t.get('name', '')
        rows = int(t.get('rows', 0) or 0)
        if not name or rows == 0:
            continue
        
        # Limit large tables
        limit = 10000 if rows > 10000 else None
        count = export_table(name, conn, limit)
        total_rows += count
        total_tables += 1
    
    conn.close()
    
    db_size = LOCAL_DB.stat().st_size / (1024*1024)
    print(f"\nDone! {total_tables} tables, {total_rows} rows, {db_size:.1f} MB")

if __name__ == "__main__":
    main()
