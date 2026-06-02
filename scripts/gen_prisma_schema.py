#!/usr/bin/env python3
"""
Generate Prisma schema from the exported SQLite database.
"""

import sqlite3
from pathlib import Path

DB_PATH = "/workspace/forrest-plan-and-track/data/onetag.db"
OUTPUT = "/workspace/forrest-plan-and-track/prisma/schema.prisma"

def generate_prisma_schema():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '\\_%' ESCAPE '\\' ORDER BY name")
    tables = [row[0] for row in c.fetchall()]
    
    lines = [
        '// OneTag HMAS Sydney — Auto-generated Prisma Schema',
        '// Source: SQL Server database exported to SQLite',
        '',
        'datasource db {',
        '  provider = "sqlite"',
        '  url      = "file:../data/onetag.db"',
        '}',
        '',
    ]
    
    for table in tables:
        # Get columns
        c.execute(f'PRAGMA table_info("{table}")')
        columns = c.fetchall()
        
        if not columns:
            continue
        
        # Get first column name for potential PK
        pk_col = columns[0][1] if columns else 'id'
        
        lines.append(f'model {table} {{')
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            
            # Map to Prisma types (everything is TEXT in our export)
            prisma_type = 'String'
            
            # Sanitize column name
            safe_name = col_name
            
            field_line = f'  {safe_name} {prisma_type}'
            if pk:
                field_line += ' @id'
            if not_null and not pk:
                field_line += ''
            else:
                field_line += '?'
            
            lines.append(field_line)
        
        lines.append(f'')
        lines.append(f'  @@map("{table}")')
        lines.append(f'}}')
        lines.append('')
    
    conn.close()
    
    # Write schema
    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Generated Prisma schema with {len(tables)} models")
    print(f"Output: {OUTPUT}")

if __name__ == "__main__":
    generate_prisma_schema()
