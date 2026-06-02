#!/usr/bin/env python3
"""
OneTag HMAS Sydney — SQL Server to SQLite Export Tool (v5)
Uses SQL files for proper batch execution.
"""

import sqlite3
import subprocess
import sys
import tempfile
import os
from pathlib import Path

SSH_KEY = "/home/hermeswebui/.ssh/id_ed25519"
SSH_HOST = "root@172.17.0.1"
CONTAINER = "sqlserver-onetag"
LOCAL_DB = Path("/workspace/forrest-plan-and-track/data/onetag.db")

def run_sql(sql, timeout=300):
    """Run SQL and return raw output."""
    escaped = sql.replace("\\", "\\\\").replace("'", "''").replace("\n", " ")
    cmd = f"""ssh -i {SSH_KEY} {SSH_HOST} "docker exec -u root {CONTAINER} /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P OneTagRestore2024! -N -C -W -s ',' -Q \\"{escaped}\\"" 2>&1"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout

def run_sql_via_file(sql, timeout=300):
    """Run SQL via a file for proper batch execution."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql)
        f.flush()
        local_path = f.name
    
    try:
        # Copy to host
        subprocess.run(f"scp -i {SSH_KEY} {local_path} {SSH_HOST}:/tmp/query.sql", shell=True, capture_output=True, timeout=30)
        # Copy to container
        subprocess.run(f"ssh -i {SSH_KEY} {SSH_HOST} 'docker cp /tmp/query.sql {CONTAINER}:/tmp/query.sql'", shell=True, capture_output=True, timeout=30)
        # Run
        result = subprocess.run(
            f"""ssh -i {SSH_KEY} {SSH_HOST} "docker exec -u root {CONTAINER} /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P OneTagRestore2024! -N -C -W -s ',' -i /tmp/query.sql" 2>&1""",
            shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout
    finally:
        os.unlink(local_path)

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
            raise Exception(f"SQL error: {stripped}")
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

def create_sqlite_db():
    LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL_DB.exists():
        LOCAL_DB.unlink()
    conn = sqlite3.connect(str(LOCAL_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.commit()
    conn.close()

def export_table(table_name, conn, limit=None):
    sql = f"USE [OneTag_Sydney];\nGO\nSELECT {'TOP ' + str(limit) + ' ' if limit else ''}* FROM [{table_name}];"
    
    try:
        output = run_sql_via_file(sql)
    except Exception as e:
        print(f"  FAIL: {table_name}: {e}")
        return 0
    
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
    print(f"  {table_name}: {count:,} rows ({len(headers)} cols)")
    return count

def main():
    print("OneTag HMAS — SQL Server → SQLite Export v5")
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
    output = run_sql_via_file("""
        USE [OneTag_Sydney];
        GO
        SELECT t.name, p.rows 
        FROM sys.tables t 
        JOIN sys.partitions p ON t.object_id = p.object_id 
        WHERE t.is_ms_shipped = 0 AND p.index_id IN (0,1) AND p.rows > 0
        ORDER BY p.rows DESC;
    """)
    _, table_list = parse_output(output)
    total_tables_found = len(table_list)
    print(f"Found {total_tables_found} tables with data\n")
    
    total_rows = 0
    exported = 0
    
    for t in table_list:
        name = t.get('name', '')
        rows = int(t.get('rows', 0) or 0)
        if not name or rows == 0:
            continue
        
        # Skip very large tables (>500k rows)
        if rows > 500000:
            print(f"  SKIP: {name}: {rows:,} rows (too large)")
            continue
        
        limit = 100000 if rows > 100000 else None
        count = export_table(name, conn, limit)
        total_rows += count
        exported += 1
    
    conn.close()
    
    db_size = LOCAL_DB.stat().st_size / (1024*1024)
    print(f"\n{'='*50}")
    print(f"Export complete!")
    print(f"  Tables: {exported} / {total_tables_found}")
    print(f"  Rows: {total_rows:,}")
    print(f"  Database: {LOCAL_DB}")
    print(f"  Size: {db_size:.1f} MB")

if __name__ == "__main__":
    main()
