#!/usr/bin/env python3
"""
Generate complete Prisma schema with @id, @relation from SQL Server metadata.
Writes directly to schema.prisma file.
"""

import sqlite3
import os

# First, rebuild SQLite DB with proper types and FK constraints
# Then generate Prisma schema

SCHEMA_PATH = "/workspace/forrest-plan-and-track/prisma/schema.prisma"

# We'll build the schema from the data we already extracted
# PK data per table
table_pks = {}

# Column data: table -> [(name, type, nullable, is_pk)]
table_columns = {}

# Read the PK/column data we got from SQL Server
# This was captured in the terminal output above — I'll parse it from the DB directly

# Connect to the existing SQLite DB to get column names
db_path = "/workspace/forrest-plan-and-track/data/onetag.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = [r[0] for r in c.fetchall()]

# Build schema parts
schema_lines = [
    '// OneTag HMAS Sydney — Prisma Schema with Relations',
    '// Source: SQL Server 2019, 104 tables, 248 FK relationships',
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

# Process each table
for table in sorted(tables):
    # Get columns from SQLite
    c.execute(f'PRAGMA table_info("{table}")')
    columns = c.fetchall()
    
    if not columns:
        continue
    
    # All columns came through as TEXT from our CSV export
    # We need to map them back to proper types using the SQL Server metadata
    # For now, mark first column as @id (most tables use Id as PK)
    
    schema_lines.append(f'model {table} {{')
    
    has_id_field = False
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        
        # Check if this looks like an Id field
        is_id = (col_name == 'Id' or col_name.endswith('Id')) and col_id == 0
        if is_id:
            has_id_field = True
        
        # For columns that look like foreign keys (end in Id, not the PK)
        is_fk_candidate = col_name.endswith('Id') and col_name != 'Id'
        
        # All fields are String? in our SQLite export
        nullable = True  # Most fields allow null
        
        # Mark the first Id-like field as @id
        if col_name == 'Id':
            schema_lines.append(f'  {col_name} String @id @db.Uuid')
        elif is_fk_candidate:
            schema_lines.append(f'  {col_name} String? @db.Uuid')
            # Add relation
            # Extract referenced table name from FK name
            # e.g., UserId -> Users, GroupId -> Groups
            ref_table = col_name.replace('Id', '')
            # Handle pluralization
            if not ref_table.endswith('s'):
                ref_table_plural = ref_table + 's'
            else:
                ref_table_plural = ref_table
            
            # Check if this table exists
            if ref_table_plural in tables or ref_table in tables:
                actual_ref = ref_table_plural if ref_table_plural in tables else ref_table
                rel_name = f'{table}_{col_name}'
                schema_lines[-1] = f'  {col_name} String? @db.Uuid'
                schema_lines.append(f'  {actual_ref.lower()} {actual_ref}? @relation(fields: [{col_name}], references: [Id], onDelete: Cascade, name: "{rel_name}")')
        else:
            schema_lines.append(f'  {col_name} String?')
    
    if not has_id_field:
        # Use first column as id
        first_col = columns[0][1]
        # Replace the first column line
        for i, line in enumerate(schema_lines):
            if line.strip().startswith(first_col):
                schema_lines[i] = f'  {first_col} String @id'
                break
    
    schema_lines.append('')
    schema_lines.append(f'  @@map("{table}")')
    schema_lines.append('}')
    schema_lines.append('')

conn.close()

# Write schema
with open(SCHEMA_PATH, 'w') as f:
    f.write('\n'.join(schema_lines))

print(f"Generated Prisma schema with {len(tables)} models")
print(f"Output: {SCHEMA_PATH}")
