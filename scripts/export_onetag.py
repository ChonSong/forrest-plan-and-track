#!/usr/bin/env python3
"""
OneTag HMAS Sydney — SQL Server to SQLite Export Tool
Exports data from the restored SQL Server database to a local SQLite database
for browsing with Prisma Studio or any SQLite viewer.

Usage: python3 export_onetag.py [--full | --summary-only]
"""

import sqlite3
import json
import sys
import subprocess
import os
from pathlib import Path

# Configuration
SSH_KEY = "/home/hermeswebui/.ssh/id_ed25519"
SSH_HOST = "root@172.17.0.1"
SQL_SERVER = "localhost"
SQL_USER = "SA"
SQL_PASS = "OneTagRestore2024!"
CONTAINER = "sqlserver-onetag"
LOCAL_DB = Path("/workspace/forrest-plan-and-track/data/onetag.db")

def run_sql_on_host(sql):
    """Run a SQL command on the host via SSH and return the output."""
    cmd = f"""ssh -i {SSH_KEY} {SSH_HOST} "docker exec -u root {CONTAINER} /opt/mssql-tools18/bin/sqlcmd -S {SQL_SERVER} -U {SQL_USER} -P {SQL_PASS} -N -C -Q \\"{sql.replace('"', '\\\\"')}\\"" 2>&1"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    return result.stdout, result.returncode

def run_sql_file_on_host(sql_file):
    """Run a SQL file on the host."""
    # Copy file to container
    subprocess.run(f"scp -i {SSH_KEY} {sql_file} {SSH_HOST}:/tmp/query.sql", shell=True, capture_output=True, timeout=30)
    cmd = f"""ssh -i {SSH_KEY} {SSH_HOST} "docker cp /tmp/query.sql {CONTAINER}:/tmp/query.sql && docker exec -u root {CONTAINER} /opt/mssql-tools18/bin/sqlcmd -S {SQL_SERVER} -U {SQL_USER} -P {SQL_PASS} -N -C -i /tmp/query.sql" 2>&1"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    return result.stdout, result.returncode

def parse_sqlcmd_output(output):
    """Parse sqlcmd -N -C output into list of dicts."""
    lines = [l for l in output.split('\n') if l.strip() and not l.startswith('(') and 'rows affected' not in l]
    if not lines:
        return []
    
    # First line is headers
    headers = [h.strip() for h in lines[0].split('  ') if h.strip()]
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        # Split by multiple spaces
        values = [v.strip() for v in line.split('  ') if v.strip()]
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))
    return rows

def create_sqlite_db():
    """Create the SQLite database with key tables."""
    LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL_DB.exists():
        LOCAL_DB.unlink()
    
    conn = sqlite3.connect(str(LOCAL_DB))
    c = conn.cursor()
    
    # Enable WAL mode for better concurrent access
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=OFF")  # Simplified — no FK enforcement for speed
    
    # Create tables for key entities
    tables = {
        "Systems": """
            CREATE TABLE IF NOT EXISTS Systems (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                SystemTypeId TEXT,
                SystemCategoryId TEXT,
                DepartmentId TEXT,
                IsSystem INTEGER,
                CriticalSystem INTEGER,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Areas": """
            CREATE TABLE IF NOT EXISTS Areas (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                Code TEXT,
                GroupId TEXT,
                AreaTypeId TEXT,
                DepartmentId TEXT,
                SerialisedBounds TEXT,
                SerialisedOrigin TEXT,
                ParentAreaId TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Users": """
            CREATE TABLE IF NOT EXISTS Users (
                Id TEXT PRIMARY KEY,
                UserName TEXT,
                Email TEXT,
                FirstName TEXT,
                LastName TEXT,
                DisplayName TEXT,
                DepartmentId TEXT,
                CompanyId TEXT,
                LoginAttempts INTEGER,
                AccountLocked INTEGER,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "IsolationPoints": """
            CREATE TABLE IF NOT EXISTS IsolationPoints (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                IsolationPointTypeId TEXT,
                AreaId TEXT,
                SystemId TEXT,
                SerialisedBounds TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "WorkPermits": """
            CREATE TABLE IF NOT EXISTS WorkPermits (
                Id TEXT PRIMARY KEY,
                WorkPermitTypeId TEXT,
                JobId TEXT,
                Title TEXT,
                Description TEXT,
                Status TEXT,
                ApprovedById TEXT,
                RequestedById TEXT,
                ClosureById TEXT,
                StartDate TEXT,
                EndDate TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Jobs": """
            CREATE TABLE IF NOT EXISTS Jobs (
                Id TEXT PRIMARY KEY,
                Title TEXT,
                Description TEXT,
                Status TEXT,
                DepartmentId TEXT,
                ReasonCodeId TEXT,
                StartDate TEXT,
                EndDate TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "RFIs": """
            CREATE TABLE IF NOT EXISTS RFIs (
                Id TEXT PRIMARY KEY,
                RFINumber TEXT,
                Title TEXT,
                Description TEXT,
                Status TEXT,
                RequestedById TEXT,
                ApprovedById TEXT,
                DueDate TEXT,
                CompletedDate TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "RFIIsolations": """
            CREATE TABLE IF NOT EXISTS RFIIsolations (
                Id TEXT PRIMARY KEY,
                RFIJobId TEXT,
                IsolationPointId TEXT,
                AppliedSignatureId TEXT,
                RemovalSignatureId TEXT,
                AppliedById TEXT,
                RemovedById TEXT,
                AppliedDate TEXT,
                RemovalDate TEXT,
                HoldPoint INTEGER,
                HighRisk INTEGER,
                IsApplied INTEGER,
                IsRemoved INTEGER,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Audits": """
            CREATE TABLE IF NOT EXISTS Audits (
                Id TEXT PRIMARY KEY,
                Title TEXT,
                Description TEXT,
                AuditType TEXT,
                Status TEXT,
                ApprovedById TEXT,
                ReservedById TEXT,
                SignOffUserId TEXT,
                StartDate TEXT,
                EndDate TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "AuditChecks": """
            CREATE TABLE IF NOT EXISTS AuditChecks (
                Id TEXT PRIMARY KEY,
                AuditId TEXT,
                RFIIsolationId TEXT,
                RFIJobId TEXT,
                AuditCheckType INTEGER,
                DefectFound INTEGER,
                DefectDescription TEXT,
                ActionsTaken INTEGER,
                ActionsDescription TEXT,
                TemporaryTagId TEXT,
                CheckQuestion TEXT,
                RFIId TEXT,
                AuditCheckDate TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "TemporaryTags": """
            CREATE TABLE IF NOT EXISTS TemporaryTags (
                Id TEXT PRIMARY KEY,
                TemporaryTagNumber TEXT,
                TemporaryTagState TEXT,
                AppliedSignatureId TEXT,
                RemovalSignatureId TEXT,
                PrintedUserId TEXT,
                DangerTagId TEXT,
                AppliedById TEXT,
                RemovedById TEXT,
                AppliedDate TEXT,
                RemovalDate TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "BoundaryTemplates": """
            CREATE TABLE IF NOT EXISTS BoundaryTemplates (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                BoundaryTemplateTypeId TEXT,
                IsDraft INTEGER,
                Version INTEGER,
                ApprovedById TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "SwMAs": """
            CREATE TABLE IF NOT EXISTS SwMAs (
                Id TEXT PRIMARY KEY,
                SwMATemplateId TEXT,
                Title TEXT,
                Status TEXT,
                DepartmentId TEXT,
                SwMACoordinatorId TEXT,
                ActualTotal REAL,
                QuotedTotal REAL,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Messages": """
            CREATE TABLE IF NOT EXISTS Messages (
                Id TEXT PRIMARY KEY,
                SenderUserId TEXT,
                Title TEXT,
                Body TEXT,
                MessageType TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Resources": """
            CREATE TABLE IF NOT EXISTS Resources (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                FileExtension TEXT,
                MediaType TEXT,
                Comment TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "PadLocks": """
            CREATE TABLE IF NOT EXISTS PadLocks (
                Id TEXT PRIMARY KEY,
                PadLockTypeId TEXT,
                SerialNumber TEXT,
                IsActive INTEGER,
                Comment TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Equipment": """
            CREATE TABLE IF NOT EXISTS Equipment (
                Id TEXT PRIMARY Key,
                Name TEXT,
                Description TEXT,
                SerialNumber TEXT,
                IsolationPointId TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Departments": """
            CREATE TABLE IF NOT EXISTS Departments (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Groups": """
            CREATE TABLE IF NOT EXISTS Groups (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                GroupTypeId TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Users_LoginHistory": """
            CREATE TABLE IF NOT EXISTS Users_LoginHistory (
                Id TEXT PRIMARY KEY,
                UserId TEXT,
                LoginDate TEXT,
                IpAddress TEXT,
                UserAgent TEXT,
                Success INTEGER,
                CreatedDate TEXT
            )
        """,
        "AuditLogs": """
            CREATE TABLE IF NOT EXISTS AuditLogs (
                Id TEXT PRIMARY KEY,
                AuditId TEXT,
                ResourceId TEXT,
                UserId TEXT,
                Action TEXT,
                Comment TEXT,
                UserName TEXT,
                CreatedDate TEXT
            )
        """,
        "RFILogs": """
            CREATE TABLE IF NOT EXISTS RFILogs (
                Id TEXT PRIMARY KEY,
                RFIId TEXT,
                UserId TEXT,
                Action TEXT,
                Comment TEXT,
                ResourceName TEXT,
                CreatedDate TEXT
            )
        """,
        "UserLogs": """
            CREATE TABLE IF NOT EXISTS UserLogs (
                Id TEXT PRIMARY KEY,
                UserId TEXT,
                ResourceId TEXT,
                LogAuthorUserId TEXT,
                Action TEXT,
                Comment TEXT,
                UserName TEXT,
                CreatedDate TEXT
            )
        """,
        "SwMALogs": """
            CREATE TABLE IF NOT EXISTS SwMALogs (
                Id TEXT PRIMARY KEY,
                SwMAId TEXT,
                ResourceId TEXT,
                UserId TEXT,
                Action TEXT,
                Comment TEXT,
                CreatedDate TEXT
            )
        """,
        "JobLogs": """
            CREATE TABLE IF NOT EXISTS JobLogs (
                Id TEXT PRIMARY KEY,
                JobId TEXT,
                UserId TEXT,
                Action TEXT,
                Comment TEXT,
                CreatedDate TEXT
            )
        """,
        "IsolationPointLogs": """
            CREATE TABLE IF NOT EXISTS IsolationPointLogs (
                Id TEXT PRIMARY KEY,
                IsolationPointId TEXT,
                UserId TEXT,
                Action TEXT,
                Comment TEXT,
                CreatedDate TEXT
            )
        """,
        "TemporaryTagLogs": """
            CREATE TABLE IF NOT EXISTS TemporaryTagLogs (
                Id TEXT PRIMARY KEY,
                TemporaryTagId TEXT,
                UserId TEXT,
                Action TEXT,
                Applied INTEGER,
                UserName TEXT,
                CreatedDate TEXT
            )
        """,
        "BoundaryTemplateLogs": """
            CREATE TABLE IF NOT EXISTS BoundaryTemplateLogs (
                Id TEXT PRIMARY KEY,
                BoundaryTemplateId TEXT,
                UserId TEXT,
                Action TEXT,
                Comment TEXT,
                CreatedDate TEXT
            )
        """,
        "DangerTag": """
            CREATE TABLE IF NOT EXISTS DangerTag (
                Id TEXT PRIMARY KEY,
                PrintedUserId TEXT,
                TemporaryTagId TEXT,
                DangerTagState TEXT,
                Comment TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Activities": """
            CREATE TABLE IF NOT EXISTS Activities (
                Id TEXT PRIMARY KEY,
                GroupVesselId TEXT,
                Number TEXT,
                Comment TEXT,
                Active INTEGER,
                ActivityStartDate TEXT,
                ActivityEndDate TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Companies": """
            CREATE TABLE IF NOT EXISTS Companies (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "SystemTypes": """
            CREATE TABLE IF NOT EXISTS SystemTypes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "SystemCategories": """
            CREATE TABLE IF NOT EXISTS SystemCategories (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "AreaTypes": """
            CREATE TABLE IF NOT EXISTS AreaTypes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                SecureArea INTEGER,
                HighRisk INTEGER,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "WorkPermitTypes": """
            CREATE TABLE IF NOT EXISTS WorkPermitTypes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "PadLockTypes": """
            CREATE TABLE IF NOT EXISTS PadLockTypes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                Color TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "LockoutDeviceTypes": """
            CREATE TABLE IF NOT EXISTS LockoutDeviceTypes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "GroupTypes": """
            CREATE TABLE IF NOT EXISTS GroupTypes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "IsolationPointTypes": """
            CREATE TABLE IF NOT EXISTS IsolationPointTypes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "CheckListTemplates": """
            CREATE TABLE IF NOT EXISTS CheckListTemplates (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "SwMATemplates": """
            CREATE TABLE IF NOT EXISTS SwMATemplates (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                SwMATemplateType TEXT,
                GroupId TEXT,
                Version INTEGER,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "CoordinateSystems": """
            CREATE TABLE IF NOT EXISTS CoordinateSystems (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "StandardActivities": """
            CREATE TABLE IF NOT EXISTS StandardActivities (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "ReasonCodes": """
            CREATE TABLE IF NOT EXISTS ReasonCodes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "EventLogs": """
            CREATE TABLE IF NOT EXISTS EventLogs (
                Id TEXT PRIMARY KEY,
                EventLogType TEXT,
                UserId TEXT,
                Action TEXT,
                Comment TEXT,
                CreatedDate TEXT
            )
        """,
        "UserRoles": """
            CREATE TABLE IF NOT EXISTS UserRoles (
                Id TEXT PRIMARY KEY,
                UserId TEXT,
                RoleId TEXT,
                CreatedDate TEXT
            )
        """,
        "UserPermissions": """
            CREATE TABLE IF NOT EXISTS UserPermissions (
                Id TEXT PRIMARY KEY,
                UserId TEXT,
                PermissionId TEXT,
                PermissionGroupId TEXT,
                ReadOnly INTEGER,
                SortOrder INTEGER,
                CreatedDate TEXT
            )
        """,
        "Permissions": """
            CREATE TABLE IF NOT EXISTS Permissions (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Roles": """
            CREATE TABLE IF NOT EXISTS Roles (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "PermissionGroups": """
            CREATE TABLE IF NOT EXISTS PermissionGroups (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "MessageTemplates": """
            CREATE TABLE IF NOT EXISTS MessageTemplates (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Subject TEXT,
                Body TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Assets": """
            CREATE TABLE IF NOT EXISTS Assets (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                AssetTypeId TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "AssetTypes": """
            CREATE TABLE IF NOT EXISTS AssetTypes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                Flags INTEGER,
                TotalCount REAL,
                TotalInUse REAL,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "AssetLogs": """
            CREATE TABLE IF NOT EXISTS AssetLogs (
                Id TEXT PRIMARY KEY,
                AssetTypeId TEXT,
                UserId TEXT,
                ChangeAmount REAL,
                Comment TEXT,
                CreatedDate TEXT
            )
        """,
        "EquipmentIsolations": """
            CREATE TABLE IF NOT EXISTS EquipmentIsolations (
                Id TEXT PRIMARY KEY,
                EquipmentId TEXT,
                IsolationPointId TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "IsolationPointChecks": """
            CREATE TABLE IF NOT EXISTS IsolationPointChecks (
                Id TEXT PRIMARY KEY,
                IsolationPointId TEXT,
                CheckQuestion TEXT,
                CheckResult INTEGER,
                Comment TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "IsolationPointLockoutDeviceTypes": """
            CREATE TABLE IF NOT EXISTS IsolationPointLockoutDeviceTypes (
                IsolationPointId TEXT,
                LockoutDeviceTypeId TEXT,
                PRIMARY KEY (IsolationPointId, LockoutDeviceTypeId)
            )
        """,
        "AreaSystem": """
            CREATE TABLE IF NOT EXISTS AreaSystem (
                AreasId TEXT,
                SystemsId TEXT,
                PRIMARY KEY (AreasId, SystemsId)
            )
        """,
        "SystemTypesDepartments": """
            CREATE TABLE IF NOT EXISTS SystemTypesDepartments (
                SystemTypesId TEXT,
                DepartmentsId TEXT,
                PRIMARY KEY (SystemTypesId, DepartmentsId)
            )
        """,
        "AuditCheckResource": """
            CREATE TABLE IF NOT EXISTS AuditCheckResource (
                AuditChecksId TEXT,
                ResourcesId TEXT,
                PRIMARY KEY (AuditChecksId, ResourcesId)
            )
        """,
        "SwMASAssessors": """
            CREATE TABLE IF NOT EXISTS SwMASAssessors (
                SwMAId TEXT,
                UserId TEXT,
                PRIMARY KEY (SwMAId, UserId)
            )
        """,
        "CheckListTemplateDepartments": """
            CREATE TABLE IF NOT EXISTS CheckListTemplateDepartments (
                CheckListTemplateId TEXT,
                DepartmentsId TEXT,
                PRIMARY KEY (CheckListTemplateId, DepartmentsId)
            )
        """,
        "SwMATemplateDepartments": """
            CREATE TABLE IF NOT EXISTS SwMATemplateDepartments (
                SwMATemplatesId TEXT,
                DepartmentsId TEXT,
                PRIMARY KEY (SwMATemplatesId, DepartmentsId)
            )
        """,
        "StandardActivitySystem": """
            CREATE TABLE IF NOT EXISTS StandardActivitySystem (
                StandardActivityId TEXT,
                SystemsId TEXT,
                PRIMARY KEY (StandardActivityId, SystemsId)
            )
        """,
        "ResourceSwMACheck": """
            CREATE TABLE IF NOT EXISTS ResourceSwMACheck (
                Id TEXT PRIMARY KEY,
                ResourceId TEXT,
                SwMACheckId TEXT,
                CreatedDate TEXT
            )
        """,
        "ResourceSwMA": """
            CREATE TABLE IF NOT EXISTS ResourceSwMA (
                Id TEXT PRIMARY KEY,
                ResourceId TEXT,
                SwMAId TEXT,
                CreatedDate TEXT
            )
        """,
        "ResourceWorkPermit": """
            CREATE TABLE IF NOT EXISTS ResourceWorkPermit (
                Id TEXT PRIMARY KEY,
                ResourceId TEXT,
                WorkPermitId TEXT,
                CreatedDate TEXT
            )
        """,
        "JobResource": """
            CREATE TABLE IF NOT EXISTS JobResource (
                Id TEXT PRIMARY KEY,
                JobId TEXT,
                ResourceId TEXT,
                CreatedDate TEXT
            )
        """,
        "IsolationPointResource": """
            CREATE TABLE IF NOT EXISTS IsolationPointResource (
                Id TEXT PRIMARY KEY,
                IsolationPointId TEXT,
                ResourceId TEXT,
                CreatedDate TEXT
            )
        """,
        "BoundaryTemplateResource": """
            CREATE TABLE IF NOT EXISTS BoundaryTemplateResource (
                Id TEXT PRIMARY KEY,
                BoundaryTemplateId TEXT,
                ResourceId TEXT,
                CreatedDate TEXT
            )
        """,
        "RFIResource": """
            CREATE TABLE IF NOT EXISTS RFIResource (
                Id TEXT PRIMARY KEY,
                RFIId TEXT,
                ResourceId TEXT,
                CreatedDate TEXT
            )
        """,
        "RFILockResource": """
            CREATE TABLE IF NOT EXISTS RFILockResource (
                Id TEXT PRIMARY KEY,
                RFILockId TEXT,
                ResourceId TEXT,
                CreatedDate TEXT
            )
        """,
        "UserLogins": """
            CREATE TABLE IF NOT EXISTS UserLogins (
                Id TEXT PRIMARY KEY,
                UserId TEXT,
                LoginProvider TEXT,
                ProviderKey TEXT,
                CreatedDate TEXT
            )
        """,
        "AuditTemporaryTags": """
            CREATE TABLE IF NOT EXISTS AuditTemporaryTags (
                Id TEXT PRIMARY KEY,
                AuditId TEXT,
                TemporaryTagId TEXT,
                CreatedDate TEXT
            )
        """,
        "AuditRFIJobs": """
            CREATE TABLE IF NOT EXISTS AuditRFIJobs (
                Id TEXT PRIMARY KEY,
                AuditId TEXT,
                RFIJobId TEXT,
                CreatedDate TEXT
            )
        """,
        "AuditRFIIsolations": """
            CREATE TABLE IF NOT EXISTS AuditRFIIsolations (
                Id TEXT PRIMARY KEY,
                AuditId TEXT,
                RFIIsolationId TEXT,
                CreatedDate TEXT
            )
        """,
        "AuditRFIIsolationSnapshots": """
            CREATE TABLE IF NOT EXISTS AuditRFIIsolationSnapshots (
                Id TEXT PRIMARY KEY,
                AuditId TEXT,
                RFIIsolationId TEXT,
                SnapshotDate TEXT,
                CreatedDate TEXT
            )
        """,
        "RFILocksRFIJobs": """
            CREATE TABLE IF NOT EXISTS RFILocksRFIJobs (
                Id TEXT PRIMARY KEY,
                RFILockId TEXT,
                RFIJobId TEXT,
                CreatedDate TEXT
            )
        """,
        "RFILockBoxes": """
            CREATE TABLE IF NOT EXISTS RFILockBoxes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                AreaId TEXT,
                Comment TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "LockoutDevices": """
            CREATE TABLE IF NOT EXISTS LockoutDevices (
                Id TEXT PRIMARY KEY,
                LockoutDeviceTypeId TEXT,
                SerialNumber TEXT,
                IsActive INTEGER,
                Comment TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "RFIJobs": """
            CREATE TABLE IF NOT EXISTS RFIJobs (
                Id TEXT PRIMARY KEY,
                RFIId TEXT,
                JobId TEXT,
                Status TEXT,
                LinkingUserId TEXT,
                DeLinkingUserId TEXT,
                SetToWorkCompleteSignatureId TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "RFISystem": """
            CREATE TABLE IF NOT EXISTS RFISystem (
                Id TEXT PRIMARY KEY,
                RFIId TEXT,
                SystemId TEXT,
                CreatedDate TEXT
            )
        """,
        "RFIAreas": """
            CREATE TABLE IF NOT EXISTS RFIAreas (
                Id TEXT PRIMARY KEY,
                RFIId TEXT,
                AreaId TEXT,
                CreatedDate TEXT
            )
        """,
        "IsolationPointIsolationPoint": """
            CREATE TABLE IF NOT EXISTS IsolationPointIsolationPoint (
                Id TEXT PRIMARY KEY,
                ParentIsolationPointId TEXT,
                ChildIsolationPointId TEXT,
                CreatedDate TEXT
            )
        """,
        "BoundaryTemplateItems": """
            CREATE TABLE IF NOT EXISTS BoundaryTemplateItems (
                Id TEXT PRIMARY KEY,
                BoundaryTemplateId TEXT,
                EquipmentId TEXT,
                IsolationPointId TEXT,
                SortOrder INTEGER,
                Comment TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "BoundaryTemplateSystem": """
            CREATE TABLE IF NOT EXISTS BoundaryTemplateSystem (
                Id TEXT PRIMARY KEY,
                BoundaryTemplateId TEXT,
                SystemId TEXT,
                CreatedDate TEXT
            )
        """,
        "BoundaryTemplateRFI": """
            CREATE TABLE IF NOT EXISTS BoundaryTemplateRFI (
                Id TEXT PRIMARY KEY,
                BoundaryTemplateId TEXT,
                RFIId TEXT,
                CreatedDate TEXT
            )
        """,
        "BoundaryTemplateStandardActivity": """
            CREATE TABLE IF NOT EXISTS BoundaryTemplateStandardActivity (
                Id TEXT PRIMARY KEY,
                BoundaryTemplateId TEXT,
                StandardActivityId TEXT,
                CreatedDate TEXT
            )
        """,
        "SwMATemplateItems": """
            CREATE TABLE IF NOT EXISTS SwMATemplateItems (
                Id TEXT PRIMARY KEY,
                SwMATemplateId TEXT,
                EquipmentId TEXT,
                CheckQuestion TEXT,
                SortOrder INTEGER,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "SwMAChecks": """
            CREATE TABLE IF NOT EXISTS SwMAChecks (
                Id TEXT PRIMARY KEY,
                SwMAId TEXT,
                SwMACheckTypeId TEXT,
                CheckQuestion TEXT,
                CheckResult INTEGER,
                Comment TEXT,
                AssessorId TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "SwMAJobsAdditionalDefects": """
            CREATE TABLE IF NOT EXISTS SwMAJobsAdditionalDefects (
                Id TEXT PRIMARY KEY,
                JobId TEXT,
                DefectDescription TEXT,
                CreatedDate TEXT
            )
        """,
        "SwMAJobsPreExistingDefects": """
            CREATE TABLE IF NOT EXISTS SwMAJobsPreExistingDefects (
                Id TEXT PRIMARY KEY,
                JobId TEXT,
                DefectDescription TEXT,
                CreatedDate TEXT
            )
        """,
        "SwMARegisters": """
            CREATE TABLE IF NOT EXISTS SwMARegisters (
                Id TEXT PRIMARY KEY,
                SwMAId TEXT,
                Status TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "CheckListTemplateItems": """
            CREATE TABLE IF NOT EXISTS CheckListTemplateItems (
                Id TEXT PRIMARY KEY,
                CheckListTemplateId TEXT,
                EquipmentId TEXT,
                CheckQuestion TEXT,
                SortOrder INTEGER,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "CheckListTemplateTypes": """
            CREATE TABLE IF NOT EXISTS CheckListTemplateTypes (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT
            )
        """,
        "StandardActivityItems": """
            CREATE TABLE IF NOT EXISTS StandardActivityItems (
                Id TEXT PRIMARY KEY,
                StandardActivityId TEXT,
                EquipmentId TEXT,
                Description TEXT,
                SortOrder INTEGER,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Maps": """
            CREATE TABLE IF NOT EXISTS Maps (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "Zones": """
            CREATE TABLE IF NOT EXISTS Zones (
                Id TEXT PRIMARY KEY,
                Name TEXT,
                Description TEXT,
                ZoneType TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "EventLogTransactions": """
            CREATE TABLE IF NOT EXISTS EventLogTransactions (
                Id TEXT PRIMARY KEY,
                EventLogId TEXT,
                TransactionData TEXT,
                CreatedDate TEXT
            )
        """,
        "JobWorkPermitType": """
            CREATE TABLE IF NOT EXISTS JobWorkPermitType (
                Id TEXT PRIMARY KEY,
                JobId TEXT,
                WorkPermitTypeId TEXT,
                CreatedDate TEXT
            )
        """,
        "AuditDefects": """
            CREATE TABLE IF NOT EXISTS AuditDefects (
                Id TEXT PRIMARY KEY,
                AuditId TEXT,
                IsolationPointId TEXT,
                DefectDescription TEXT,
                AuditDefectDate TEXT,
                CreatedDate TEXT,
                ModifiedDate TEXT,
                DeletedDate TEXT,
                CreatedBy TEXT,
                ModifiedBy TEXT,
                DeletedBy TEXT
            )
        """,
        "RFIIsolationResource": """
            CREATE TABLE IF NOT EXISTS RFIIsolationResource (
                Id TEXT PRIMARY KEY,
                RFIIsolationId TEXT,
                ResourceId TEXT,
                CreatedDate TEXT
            )
        """,
    }
    
    for table_name, create_sql in tables.items():
        c.execute(create_sql)
    
    # Create metadata table
    c.execute("""
        CREATE TABLE IF NOT EXISTS _metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    c.execute("INSERT INTO _metadata VALUES ('source', 'OneTag_Sydney SQL Server 2019')")
    c.execute("INSERT INTO _metadata VALUES ('exported_at', datetime('now'))")
    c.execute("INSERT INTO _metadata VALUES ('total_tables', ?)", (len(tables),))
    
    conn.commit()
    conn.close()
    print(f"Created SQLite database with {len(tables)} tables at {LOCAL_DB}")

def export_table(table_name, columns, where_clause=""):
    """Export a single table from SQL Server to SQLite."""
    col_list = ", ".join([f"[{col}]" for col in columns])
    sql = f"SELECT {col_list} FROM [{table_name}]"
    if where_clause:
        sql += f" WHERE {where_clause}"
    
    output, rc = run_sql_on_host(sql)
    if rc != 0:
        print(f"  WARNING: Failed to export {table_name}: {output[:200]}")
        return 0
    
    rows = parse_sqlcmd_output(output)
    if not rows:
        print(f"  {table_name}: 0 rows")
        return 0
    
    # Insert into SQLite
    conn = sqlite3.connect(str(LOCAL_DB))
    c = conn.cursor()
    
    placeholders = ", ".join(["?"] * len(columns))
    col_names = ", ".join([f"[{col}]" for col in columns])
    insert_sql = f"INSERT OR REPLACE INTO [{table_name}] ({col_names}) VALUES ({placeholders})"
    
    count = 0
    for row in rows:
        values = [row.get(col, None) for col in columns]
        try:
            c.execute(insert_sql, values)
            count += 1
        except Exception as e:
            pass  # Skip problematic rows
    
    conn.commit()
    conn.close()
    print(f"  {table_name}: {count} rows exported")
    return count

def export_summary_data():
    """Export summary/aggregate data for quick browsing."""
    conn = sqlite3.connect(str(LOCAL_DB))
    c = conn.cursor()
    
    # Create summary views
    summaries = {
        "summary_table_counts": """
            CREATE TABLE IF NOT EXISTS summary_table_counts AS
            SELECT 'Systems' as table_name, 0 as row_count
        """,
    }
    
    # Get actual counts from SQL Server
    count_sql = """
        USE [OneTag_Sydney];
        SELECT 
            t.name AS table_name,
            p.rows AS row_count
        FROM sys.tables t
        JOIN sys.partitions p ON t.object_id = p.object_id
        WHERE t.is_ms_shipped = 0 AND p.index_id IN (0,1)
        ORDER BY p.rows DESC
    """
    
    output, rc = run_sql_on_host(count_sql)
    if rc == 0:
        rows = parse_sqlcmd_output(output)
        
        c.execute("CREATE TABLE IF NOT EXISTS summary_table_counts (table_name TEXT, row_count INTEGER)")
        c.execute("DELETE FROM summary_table_counts")
        
        for row in rows:
            c.execute("INSERT INTO summary_table_counts VALUES (?, ?)", 
                      (row.get('table_name', ''), int(row.get('row_count', 0) or 0)))
        
        conn.commit()
        print(f"\nExported table count summary: {len(rows)} tables")
    
    conn.close()

def main():
    print("=" * 60)
    print("OneTag HMAS Sydney — SQL Server to SQLite Export")
    print("=" * 60)
    
    # Check SQL Server is accessible
    print("\n1. Checking SQL Server connectivity...")
    output, rc = run_sql_on_host("SELECT 1")
    if rc != 0:
        print("ERROR: Cannot connect to SQL Server. Is the container running?")
        print("Run: docker start sqlserver-onetag")
        sys.exit(1)
    print("   OK")
    
    # Create SQLite database
    print("\n2. Creating SQLite database...")
    create_sqlite_db()
    
    # Export summary data
    print("\n3. Exporting table count summary...")
    export_summary_data()
    
    # Export key tables (prioritized by row count and importance)
    print("\n4. Exporting key tables...")
    
    key_tables = [
        ("Departments", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("SystemTypes", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("SystemCategories", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("AreaTypes", ["Id", "Name", "Description", "SecureArea", "HighRisk", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("GroupTypes", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("WorkPermitTypes", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("PadLockTypes", ["Id", "Name", "Description", "Color", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("LockoutDeviceTypes", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("IsolationPointTypes", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("ReasonCodes", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Groups", ["Id", "Name", "Description", "GroupTypeId", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Companies", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Roles", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Permissions", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("PermissionGroups", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Users", ["Id", "UserName", "Email", "FirstName", "LastName", "DisplayName", "DepartmentId", "CompanyId", "LoginAttempts", "AccountLocked", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Systems", ["Id", "Name", "Description", "SystemTypeId", "SystemCategoryId", "DepartmentId", "IsSystem", "CriticalSystem", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Areas", ["Id", "Name", "Description", "Code", "GroupId", "AreaTypeId", "DepartmentId", "SerialisedBounds", "SerialisedOrigin", "ParentAreaId", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("IsolationPoints", ["Id", "Name", "Description", "IsolationPointTypeId", "AreaId", "SystemId", "SerialisedBounds", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Equipment", ["Id", "Name", "Description", "SerialNumber", "IsolationPointId", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("PadLocks", ["Id", "PadLockTypeId", "SerialNumber", "IsActive", "Comment", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("LockoutDevices", ["Id", "LockoutDeviceTypeId", "SerialNumber", "IsActive", "Comment", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("WorkPermits", ["Id", "WorkPermitTypeId", "JobId", "Title", "Description", "Status", "ApprovedById", "RequestedById", "ClosureById", "StartDate", "EndDate", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Jobs", ["Id", "Title", "Description", "Status", "DepartmentId", "ReasonCodeId", "StartDate", "EndDate", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("RFIs", ["Id", "RFINumber", "Title", "Description", "Status", "RequestedById", "ApprovedById", "DueDate", "CompletedDate", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("RFIIsolations", ["Id", "RFIJobId", "IsolationPointId", "AppliedSignatureId", "RemovalSignatureId", "AppliedById", "RemovedById", "AppliedDate", "RemovalDate", "HoldPoint", "HighRisk", "IsApplied", "IsRemoved", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("RFILocks", ["Id", "RFIJobId", "PadLockId", "LockOnSignatureId", "LockOffSignatureId", "LockOnDate", "LockOffDate", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("RFILockBoxes", ["Id", "Name", "AreaId", "Comment", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Audits", ["Id", "Title", "Description", "AuditType", "Status", "ApprovedById", "ReservedById", "SignOffUserId", "StartDate", "EndDate", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("AuditChecks", ["Id", "AuditId", "RFIIsolationId", "RFIJobId", "AuditCheckType", "DefectFound", "DefectDescription", "ActionsTaken", "ActionsDescription", "TemporaryTagId", "CheckQuestion", "RFIId", "AuditCheckDate", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("TemporaryTags", ["Id", "TemporaryTagNumber", "TemporaryTagState", "AppliedSignatureId", "RemovalSignatureId", "PrintedUserId", "DangerTagId", "AppliedById", "RemovedById", "AppliedDate", "RemovalDate", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("BoundaryTemplates", ["Id", "Name", "Description", "BoundaryTemplateTypeId", "IsDraft", "Version", "ApprovedById", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("SwMATemplates", ["Id", "Name", "Description", "SwMATemplateType", "GroupId", "Version", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("SwMAs", ["Id", "SwMATemplateId", "Title", "Status", "DepartmentId", "SwMACoordinatorId", "ActualTotal", "QuotedTotal", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("SwMAChecks", ["Id", "SwMAId", "SwMACheckTypeId", "CheckQuestion", "CheckResult", "Comment", "AssessorId", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Messages", ["Id", "SenderUserId", "Title", "Body", "MessageType", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Resources", ["Id", "Name", "Description", "FileExtension", "MediaType", "Comment", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Activities", ["Id", "GroupVesselId", "Number", "Comment", "Active", "ActivityStartDate", "ActivityEndDate", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("DangerTag", ["Id", "PrintedUserId", "TemporaryTagId", "DangerTagState", "Comment", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("UserLoginHistory", ["Id", "UserId", "LoginDate", "IpAddress", "UserAgent", "Success", "CreatedDate"]),
        ("AuditLogs", ["Id", "AuditId", "ResourceId", "UserId", "Action", "Comment", "UserName", "CreatedDate"]),
        ("RFILogs", ["Id", "RFIId", "UserId", "Action", "Comment", "ResourceName", "CreatedDate"]),
        ("UserLogs", ["Id", "UserId", "ResourceId", "LogAuthorUserId", "Action", "Comment", "UserName", "CreatedDate"]),
        ("SwMALogs", ["Id", "SwMAId", "ResourceId", "UserId", "Action", "Comment", "CreatedDate"]),
        ("JobLogs", ["Id", "JobId", "UserId", "Action", "Comment", "CreatedDate"]),
        ("IsolationPointLogs", ["Id", "IsolationPointId", "UserId", "Action", "Comment", "CreatedDate"]),
        ("TemporaryTagLogs", ["Id", "TemporaryTagId", "UserId", "Action", "Applied", "UserName", "CreatedDate"]),
        ("BoundaryTemplateLogs", ["Id", "BoundaryTemplateId", "UserId", "Action", "Comment", "CreatedDate"]),
        ("EventLogs", ["Id", "EventLogType", "UserId", "Action", "Comment", "CreatedDate"]),
        ("UserRoles", ["Id", "UserId", "RoleId", "CreatedDate"]),
        ("UserPermissions", ["Id", "UserId", "PermissionId", "PermissionGroupId", "ReadOnly", "SortOrder", "CreatedDate"]),
        ("UserLogins", ["Id", "UserId", "LoginProvider", "ProviderKey", "CreatedDate"]),
        ("AssetTypes", ["Id", "Name", "Description", "Flags", "TotalCount", "TotalInUse", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("Assets", ["Id", "Name", "Description", "AssetTypeId", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("AssetLogs", ["Id", "AssetTypeId", "UserId", "ChangeAmount", "Comment", "CreatedDate"]),
        ("EquipmentIsolations", ["Id", "EquipmentId", "IsolationPointId", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("IsolationPointChecks", ["Id", "IsolationPointId", "CheckQuestion", "CheckResult", "Comment", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("BoundaryTemplateItems", ["Id", "BoundaryTemplateId", "EquipmentId", "IsolationPointId", "SortOrder", "Comment", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("SwMATemplateItems", ["Id", "SwMATemplateId", "EquipmentId", "CheckQuestion", "SortOrder", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("CheckListTemplates", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("CheckListTemplateItems", ["Id", "CheckListTemplateId", "EquipmentId", "CheckQuestion", "SortOrder", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("StandardActivities", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("StandardActivityItems", ["Id", "StandardActivityId", "EquipmentId", "Description", "SortOrder", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("CoordinateSystems", ["Id", "Name", "Description", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("MessageTemplates", ["Id", "Name", "Subject", "Body", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("RFIJobs", ["Id", "RFIId", "JobId", "Status", "LinkingUserId", "DeLinkingUserId", "SetToWorkCompleteSignatureId", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("RFISystem", ["Id", "RFIId", "SystemId", "CreatedDate"]),
        ("RFIAreas", ["Id", "RFIId", "AreaId", "CreatedDate"]),
        ("RFILocksRFIJobs", ["Id", "RFILockId", "RFIJobId", "CreatedDate"]),
        ("AuditTemporaryTags", ["Id", "AuditId", "TemporaryTagId", "CreatedDate"]),
        ("AuditRFIJobs", ["Id", "AuditId", "RFIJobId", "CreatedDate"]),
        ("AuditRFIIsolations", ["Id", "AuditId", "RFIIsolationId", "CreatedDate"]),
        ("AuditDefects", ["Id", "AuditId", "IsolationPointId", "DefectDescription", "AuditDefectDate", "CreatedDate", "ModifiedDate", "DeletedDate", "CreatedBy", "ModifiedBy", "DeletedBy"]),
        ("AreaSystem", ["AreasId", "SystemsId"]),
        ("SystemTypesDepartments", ["SystemTypesId", "DepartmentsId"]),
        ("AuditCheckResource", ["AuditChecksId", "ResourcesId"]),
        ("SwMASAssessors", ["SwMAId", "UserId"]),
        ("CheckListTemplateDepartments", ["CheckListTemplateId", "DepartmentsId"]),
        ("SwMATemplateDepartments", ["SwMATemplatesId", "DepartmentsId"]),
        ("StandardActivitySystem", ["StandardActivityId", "SystemsId"]),
    ]
    
    total_rows = 0
    for table_info in key_tables:
        if len(table_info) == 2:
            table_name, columns = table_info
        else:
            table_name, columns = table_info[0], table_info[1]
        rows = export_table(table_name, columns)
        total_rows += rows
    
    print(f"\n   Total: {total_rows} rows exported across {len(key_tables)} tables")
    
    # Final summary
    print("\n5. Export complete!")
    print(f"   Database: {LOCAL_DB}")
    print(f"   Size: {LOCAL_DB.stat().st_size / 1024:.1f} KB")
    print(f"\n   To browse: open {LOCAL_DB} with any SQLite viewer")
    print(f"   Or run: npx prisma studio (from the prisma/ directory)")

if __name__ == "__main__":
    main()
