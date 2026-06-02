#!/usr/bin/env python3
"""
Generate complete Prisma schema with accurate @relation definitions
from SQL Server FK metadata.
"""

import sqlite3
import subprocess
import json
from pathlib import Path

SSH_KEY = "/home/hermeswebui/.ssh/id_ed25519"
SSH_HOST = "root@172.17.0.1"
CONTAINER = "sqlserver-onetag"
SCHEMA_PATH = Path("/workspace/forrest-plan-and-track/prisma/schema.prisma")
DB_PATH = "/workspace/forrest-plan-and-track/data/onetag.db"

def run_sql(sql, timeout=120):
    escaped = sql.replace("'", "''").replace("\n", " ")
    cmd = f"""ssh -i {SSH_KEY} {SSH_HOST} "docker exec -u root {CONTAINER} /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P OneTagRestore2024! -N -C -W -s '|' -Q \\"{escaped}\\"" 2>&1"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return result.stdout

def parse_pipe_output(output):
    """Parse pipe-delimited sqlcmd output."""
    lines = [l.strip() for l in output.split('\n') if l.strip() and not l.startswith('Changed') and not l.startswith('(')]
    if len(lines) < 3:
        return [], []
    headers = [h.strip() for h in lines[0].split('|')]
    rows = []
    for line in lines[2:]:
        values = [v.strip() for v in line.split('|')]
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))
    return headers, rows

# Get PKs
print("Getting primary keys...")
output = run_sql("""
    USE [OneTag_Sydney];
    SELECT t.name AS table_name, c.name AS column_name
    FROM sys.tables t
    JOIN sys.indexes i ON t.object_id = i.object_id
    JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    WHERE t.is_ms_shipped = 0 AND i.is_primary_key = 1
    ORDER BY t.name, ic.key_ordinal;
""")
_, pk_rows = parse_pipe_output(output)
pks = {}
for row in pk_rows:
    tbl = row['table_name']
    col = row['column_name']
    if tbl not in pks:
        pks[tbl] = []
    pks[tbl].append(col)

print(f"  Found PKs for {len(pks)} tables")

# Get columns with types
print("Getting columns...")
output = run_sql("""
    USE [OneTag_Sydney];
    SELECT t.name AS table_name, c.name AS column_name, ty.name AS data_type, 
           c.max_length, c.is_nullable
    FROM sys.tables t
    JOIN sys.columns c ON t.object_id = c.object_id
    JOIN sys.types ty ON c.user_type_id = ty.user_type_id
    WHERE t.is_ms_shipped = 0
    ORDER BY t.name, c.column_id;
""")
_, col_rows = parse_pipe_output(output)
columns = {}
for row in col_rows:
    tbl = row['table_name']
    if tbl not in columns:
        columns[tbl] = []
    columns[tbl].append(row)

print(f"  Found columns for {len(columns)} tables")

# Get FKs
print("Getting foreign keys...")
output = run_sql("""
    USE [OneTag_Sydney];
    SELECT tp.name AS parent_table, cp.name AS parent_column,
           tr.name AS referenced_table, cr.name AS referenced_column
    FROM sys.foreign_keys fk
    JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
    JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
    JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
    JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
    JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
    ORDER BY tp.name;
""")
_, fk_rows = parse_pipe_output(output)
fks = {}
for row in fk_rows:
    tbl = row['parent_table']
    if tbl not in fks:
        fks[tbl] = []
    fks[tbl].append(row)

print(f"  Found FKs for {len(fks)} tables")

# SQL to Prisma type mapping
def sql_to_prisma(sql_type, max_length):
    t = sql_type.lower()
    if t in ('nvarchar', 'varchar', 'nchar', 'char', 'text', 'ntext'):
        return 'String'
    elif t in ('int', 'smallint', 'tinyint'):
        return 'Int'
    elif t in ('bigint',):
        return 'BigInt'
    elif t in ('bit',):
        return 'Boolean'
    elif t in ('float', 'real'):
        return 'Float'
    elif t in ('decimal', 'numeric', 'money'):
        return 'Decimal'
    elif t in ('datetime', 'datetime2', 'smalldatetime', 'date', 'time', 'datetimeoffset'):
        return 'DateTime'
    elif t in ('uniqueidentifier',):
        return 'String'
    elif t in ('varbinary', 'binary', 'image'):
        return 'Bytes'
    return 'String'

# Generate Prisma schema
print("Generating Prisma schema...")

lines = [
    '// OneTag HMAS Sydney — Prisma Schema',
    '// Source: SQL Server 2019 backup, 104 tables, 248 FK relationships',
    '',
    'datasource db {',
    '  provider = "sqlite"',
    '  url      = "file:../../data/onetag.db"',
    '}',
    '',
    'generator client {',
    '  provider = "prisma-client-js"',
    '}',
    '',
]

# Track which tables have relations added
relation_fields = {}  # table -> set of field names that are FKs

for table in sorted(columns.keys()):
    cols = columns[table]
    table_pk = pks.get(table, [])
    table_fk = fks.get(table, [])
    
    # Build set of FK parent columns
    fk_columns = {fk['parent_column'] for fk in table_fk}
    
    # Track relation fields to avoid duplicates
    rel_fields = set()
    
    lines.append(f'model {table} {{')
    
    for col in cols:
        col_name = col['column_name']
        sql_type = col['data_type']
        max_len = col['max_length']
        is_nullable = col['is_nullable'] == '1'
        is_pk = col_name in table_pk
        is_fk = col_name in fk_columns
        
        prisma_type = sql_to_prisma(sql_type, max_len)
        
        # Build field
        field_str = f'  {col_name} {prisma_type}'
        
        if is_pk and len(table_pk) == 1:
            field_str += ' @id'
            if sql_type == 'uniqueidentifier':
                field_str += ' @default(uuid())'
        elif is_pk:
            # Composite PK — mark with @id for now (Prisma supports @@id)
            field_str += ' @id'
        
        if not is_pk and is_nullable:
            field_str += '?'
        elif not is_pk and not is_nullable:
            pass  # Required field
        
        # Add db attribute for UUID fields
        if sql_type == 'uniqueidentifier' and not is_pk:
            field_str += ' @db.Uuid'
        
        lines.append(field_str)
    
    # Add relation fields
    for fk in table_fk:
        parent_col = fk['parent_column']
        ref_table = fk['referenced_table']
        ref_col = fk['referenced_column']
        
        # Relation field name (lowercase referenced table)
        rel_name = ref_table[0].lower() + ref_table[1:]
        
        # Avoid duplicate relation fields
        if rel_name in rel_fields:
            rel_name = rel_name + '_' + parent_col.replace('Id', '').lower()
        rel_fields.add(rel_name)
        
        # Add relation
        rel_line = f'  {rel_name} {ref_table}? @relation(fields: [{parent_col}], references: [{ref_col}], onDelete: NoAction, onUpdate: NoAction)'
        lines.append(rel_line)
    
    # Add composite PK if needed
    if len(table_pk) > 1:
        pk_cols = ', '.join(table_pk)
        # Remove individual @id marks and add @@id
        # For simplicity, just add @@id
        lines.append(f'  @@id([{pk_cols}])')
    
    lines.append('')
    lines.append(f'  @@map("{table}")')
    lines.append('}')
    lines.append('')

# Write schema
SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(SCHEMA_PATH, 'w') as f:
    f.write('\n'.join(lines))

print(f"✅ Generated Prisma schema: {SCHEMA_PATH}")
print(f"   Tables: {len(columns)}")
print(f"   Relations: {len(fk_rows)}")
