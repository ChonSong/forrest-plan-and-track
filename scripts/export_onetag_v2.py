#!/usr/bin/env python3
"""
OneTag HMAS Sydney — SQL Server to SQLite Export Tool (v2)
Uses CSV format for reliable parsing.

Usage: python3 export_onetag_v2.py
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

def run_sql_csv(sql, timeout=120):
    """Run SQL and return CSV output."""
    # Use sqlcmd with -s comma separator and -W (remove trailing spaces)
    escaped = sql.replace("'", "''")
    cmd = f"""ssh -i {SSH_KEY} {SSH_HOST} "docker exec -u root {CONTAINER} /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P OneTagRestore2024! -N -C -W -s ',' -Q \\"{escaped}\\"" 2>&1"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout, result.returncode

def parse_csv_output(output):
    """Parse CSV output from sqlcmd."""
    lines = [l for l in output.split('\n') if l.strip()]
    if not lines:
        return [], []
    
    reader = csv.reader(io.StringIO('\n'.join(lines)))
    rows = list(reader)
    if not rows:
        return [], []
    
    headers = [h.strip() for h in rows[0]]
    data_rows = []
    for row in rows[1:]:
        if len(row) == len(headers):
            data_rows.append(dict(zip(headers, row)))
    return headers, data_rows

def create_sqlite_db():
    """Create SQLite database."""
    LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL_DB.exists():
        LOCAL_DB.unlink()
    conn = sqlite3.connect(str(LOCAL_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.commit()
    conn.close()
    print(f"Created: {LOCAL_DB}")

def export_table(table_name, conn):
    """Export a single table."""
    sql = f"SELECT * FROM [{table_name}]"
    output, rc = run_sql_csv(sql, timeout=300)
    
    if rc != 0:
        print(f"  FAIL: {table_name}: {output[:100]}")
        return 0
    
    headers, rows = parse_csv_output(output)
    if not headers:
        print(f"  EMPTY: {table_name}")
        return 0
    
    # Create table dynamically
    c = conn.cursor()
    col_defs = ", ".join([f'"{h}" TEXT' for h in headers])
    c.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    c.execute(f'CREATE TABLE "{table_name}" ({col_defs})')
    
    # Insert data
    placeholders = ", ".join(["?"] * len(headers))
    insert_sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'
    
    count = 0
    for row in rows:
        values = [row.get(h, None) for h in headers]
        try:
            c.execute(insert_sql, values)
            count += 1
        except Exception as e:
            pass
    
    conn.commit()
    print(f"  {table_name}: {count} rows, {len(headers)} cols")
    return count

def main():
    print("=" * 60)
    print("OneTag HMAS Sydney — SQL Server → SQLite Export v2")
    print("=" * 60)
    
    # Check connectivity
    print("\n1. Checking SQL Server...")
    output, rc = run_sql_csv("SELECT 1 AS x")
    if rc != 0:
        print("ERROR: SQL Server not responding")
        sys.exit(1)
    print("   OK")
    
    # Create DB
    print("\n2. Creating SQLite database...")
    create_sqlite_db()
    conn = sqlite3.connect(str(LOCAL_DB))
    
    # Get table list with row counts
    print("\n3. Getting table list...")
    output, rc = run_sql_csv("""
        USE [OneTag_Sydney];
        SELECT t.name, p.rows 
        FROM sys.tables t 
        JOIN sys.partitions p ON t.object_id = p.object_id 
        WHERE t.is_ms_shipped = 0 AND p.index_id IN (0,1) AND p.rows > 0
        ORDER BY p.rows DESC
    """)
    headers, table_list = parse_csv_output(output)
    print(f"   Found {len(table_list)} tables with data")
    
    # Export each table
    print("\n4. Exporting tables...")
    total_rows = 0
    total_tables = 0
    
    for table_info in table_list:
        table_name = table_info.get('name', '')
        row_count = int(table_info.get('rows', 0) or 0)
        
        if not table_name or row_count == 0:
            continue
        
        # For very large tables, limit to first 10000 rows
        if row_count > 10000:
            sql = f"SELECT TOP 10000 * FROM [{table_name}]"
            output, rc = run_sql_csv(sql, timeout=300)
            if rc == 0:
                headers, rows = parse_csv_output(output)
                if headers:
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
                    print(f"  {table_name}: {count} rows (of {row_count} total), {len(headers)} cols")
                    total_rows += count
                    total_tables += 1
        else:
            count = export_table(table_name, conn)
            total_rows += count
            total_tables += 1
    
    # Summary
    conn.close()
    db_size = LOCAL_DB.stat().st_size / (1024*1024)
    print(f"\n5. Export complete!")
    print(f"   Tables: {total_tables}")
    print(f"   Total rows: {total_rows}")
    print(f"   Database: {LOCAL_DB}")
    print(f"   Size: {db_size:.1f} MB")

if __name__ == "__main__":
    main()
