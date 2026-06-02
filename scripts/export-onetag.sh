#!/bin/bash
# OneTag HMAS — Export from SQL Server to SQLite for Prisma Studio browsing
# Run this script to sync data from the live SQL Server to local SQLite

set -e

HOST="172.17.0.1"
BAK_DIR="/home/sean/workspace"
MSSQL_DATA="/home/sean/mssql-data"
LOCAL_DB="/workspace/forrest-plan-and-track/data/onetag.db"
PRISMA_DIR="/workspace/forrest-plan-and-track/prisma"

echo "=== OneTag HMAS: SQL Server → SQLite Export ==="

# Check SQL Server is running
echo "Checking SQL Server..."
if ! ssh -i /home/hermeswebui/.ssh/id_ed25519 root@$HOST "docker exec -u root sqlserver-onetag /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P OneTagRestore2024! -N -C -Q 'SELECT 1'" 2>/dev/null | grep -q 1; then
    echo "ERROR: SQL Server not responding. Start it first:"
    echo "  docker start sqlserver-onetag"
    exit 1
fi
echo "SQL Server OK."

# Get the list of tables with data
echo "Getting table list..."
TABLES=$(ssh -i /home/hermeswebui/.ssh/id_ed25519 root@$HOST "docker exec -u root sqlserver-onetag /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P OneTagRestore2024! -N -C -Q \"
USE [OneTag_Sydney];
SELECT t.name FROM sys.tables t JOIN sys.partitions p ON t.object_id = p.object_id WHERE t.is_ms_shipped = 0 AND p.index_id IN (0,1) AND p.rows > 0 ORDER BY t.name;
\"" 2>/dev/null | grep -v "^$" | grep -v "rows affected")

echo "Tables with data:"
echo "$TABLES"

# Generate SQLite schema from Prisma
echo "Generating SQLite schema..."
cd "$PRISMA_DIR"
npx prisma generate 2>&1 | tail -3
npx prisma db push --skip-generate 2>&1 | tail -3

echo "=== Export complete ==="
echo "Open Prisma Studio with: npx prisma studio"
