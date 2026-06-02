#!/usr/bin/env python3
"""
Generate a proper Prisma schema with relationships from SQL Server metadata.
"""

# Foreign key relationships extracted from SQL Server
# Format: (parent_table, parent_column, referenced_table, referenced_column)
# Primary keys: column with is_pk=1 for each table

# Maps SQL types to Prisma types
def sql_to_prisma(sql_type, max_length):
    """Map SQL Server types to Prisma types."""
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
    elif t in ('decimal', 'numeric', 'money', 'smallmoney'):
        return 'Decimal'
    elif t in ('datetime', 'datetime2', 'smalldatetime', 'date', 'time'):
        return 'DateTime'
    elif t in ('datetimeoffset',):
        return 'DateTime'
    elif t in ('uniqueidentifier',):
        return 'String'  # UUID as String
    elif t in ('varbinary', 'binary', 'image'):
        return 'Bytes'
    else:
        return 'String'  # Default to String for unknown types

# Data from SQL Server
# PK data: table_name -> column_name
pks = {
    'Activities': 'Id',
    'AreaSystem': None,  # composite key
    'AreaTypes': 'Id',
    'Areas': 'Id',
    'AssetLogs': 'Id',
    'AssetTypes': 'Id',
    'AuditCheckResource': None,  # composite
    'AuditChecks': 'Id',
    'AuditDefects': 'Id',
    'AuditLogs': 'Id',
    'AuditRFIIsolationSnapshots': 'Id',
    'AuditRFIIsolations': None,  # composite
    'AuditRFIJobs': None,  # composite
    'AuditRFIs': None,  # composite
    'Audits': 'Id',
    'AuditTemporaryTags': 'Id',
    'BoundaryTemplateItems': 'Id',
    'BoundaryTemplateLogs': 'Id',
    'BoundaryTemplateResource': 'Id',
    'BoundaryTemplateRFI': 'Id',
    'BoundaryTemplates': 'Id',
    'BoundaryTemplateStandardActivity': 'Id',
    'BoundaryTemplateSystem': None,  # composite
    'CheckListTemplateDepartments': None,  # composite
    'CheckListTemplateItems': 'Id',
    'CheckListTemplates': 'Id',
    'CheckListTemplateTypes': 'Id',
    'Companies': 'Id',
    'Departments': 'Id',
    'Equipment': 'Id',
    'EquipmentIsolations': 'Id',
    'EventLogs': 'Id',
    'ResourceSwMACheck': 'Id',
    'ResourceSwMA': 'Id',
}

# Column data: table_name -> [(col_name, sql_type, max_length, is_nullable, is_pk)]
# This will be populated from the full extraction
# For now, let me write the schema key parts manually based on what we know

print("Generating Prisma schema...")
print(f"Tables with PKs: {len(pks)}")
