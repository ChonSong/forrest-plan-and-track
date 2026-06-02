# OneTag HMAS Sydney — Database Analysis

> **Source:** SQL Server backup file `OneTag_HMAS SYDNEY_ANON.bak` (2.45 GB)
> **Database name:** `OneTag_Sydney`
> **Server:** `BC-DIRELAND-MB\MSSQLSERVER2019` (SQL Server 2019)
> **Original file paths:**
> - Data: `C:\Program Files\Microsoft SQL Server\MSSQL15.MSSQLSERVER2019\MSSQL\DATA\OneTag_Sydney.mdf`
> - Log: `C:\Program Files\Microsoft SQL Server\MSSQL15.MSSQLSERVER2019\MSSQL\DATA\OneTag_Sydney_log.ldf`
> **Azure AD user:** `AzureAD\DarrenIreland`

## Domain

**HMAS (Health, Safety, Environmental, Asset Management)** system for Sydney operations. This is an industrial safety management platform tracking:

- **Isolation management** (lockout/tagout procedures for equipment)
- **Work permits** (authorization for hazardous work)
- **Audits & inspections** (safety compliance checks)
- **Temporary tags** (danger tags, out-of-service tags)
- **Boundary templates** (isolation boundary definitions)
- **RFI (Request for Information)** tracking
- **User management** with roles, permissions, departments

## Entity Inventory (User Tables)

Based on backup header string extraction. Tables grouped by domain area.

### Core System
| Table | PK | Notes |
|-------|----|-------|
| `Systems` | `PK_Systems` (`SystemId`) | Master system registry |
| `SystemTypes` | `PK_SystemTypes` (`SystemTypeId`) | System classification |
| `SystemCategories` | `PK_SystemCategories` (`SystemCategoryId`) | System categorization |
| `AreaSystem` | `PK_AreaSystem` | Area-to-system mapping |
| `Areas` | — | Organizational areas |
| `AreaTypes` | `PK_AreaTypes` (`AreaTypeId`) | Area classification |
| `Departments` | — | Organizational departments |

### Isolation Management (Lockout/Tagout)
| Table | PK | Notes |
|-------|----|-------|
| `IsolationPoints` | — | Points where equipment can be isolated |
| `IsolationPointTypes` | `PK_IsolationPointTypes` | Classification of isolation points |
| `IsolationPointChecks` | — | Verification checks for isolations |
| `IsolationPointLogs` | — | Audit trail for isolation events |
| `IsolationPointLockoutDeviceTypes` | `PK_IsolationPointLockoutDeviceTypes` | Which lockout devices apply to which isolation points |
| `RFIIsolations` | `PK_RFIIsolations` | RFI-linked isolations |
| `RFIIsolationSnapshots` | — | Point-in-time snapshots of RFI isolations |
| `RFILocks` | — | Lock records for RFI process |
| `RFILockBoxes` | — | Physical lock boxes |
| `RFILocksRFIJobs` | — | Junction: locks to RFI jobs |
| `RFILogs` | — | RFI event log |

### Lockout Devices & Padlocks
| Table | PK | Notes |
|-------|----|-------|
| `PadLocks` | — | Physical padlock inventory |
| `PadLockTypes` | `PK_PadLockTypes` (`PadLockTypeId`) | Padlock classification |
| `LockoutDevices` | — | Generic lockout devices |
| `LockoutDeviceTypes` | `PK_LockoutDeviceTypes` (`LockOutDeviceTypeId`) | Device type classification |

### Work Permits
| Table | PK | Notes |
|-------|----|-------|
| `WorkPermits` | — | Work authorization records |
| `WorkPermitTypes` | `PK_WorkPermitTypes` (`WorkPermitTypeId`) | Permit classification |
| `JobWorkPermitType` | `PK_JobWorkPermitType` | Job-to-permit type mapping |

### Boundary Templates (Isolation Boundaries)
| Table | PK | Notes |
|-------|----|-------|
| `BoundaryTemplates` | `PK_BoundaryTemplates` (`BoundaryTemplateId`) | Reusable isolation boundary definitions |
| `BoundaryTemplateItems` | `PK_BoundaryTemplateItems` | Items within a boundary template |
| `BoundaryTemplateLogs` | — | Change history for boundary templates |
| `BoundaryTemplateRFI` | `PK_BoundaryTemplateRFI` | Boundary template to RFI linkage |
| `BoundaryTemplateStandardActivity` | `PK_BoundaryTemplateStandardActivity` | Standard activities for boundaries |
| `BoundaryTemplateResource` | — | Resource assignments for boundaries |

### SwMA (Safe Work Method Assessment / Safety Work Method Analysis)
| Table | PK | Notes |
|-------|----|-------|
| `SwMATemplates` | `PK_SwMATemplates` (`SwMATemplateId`) | Reusable safety assessment templates |
| `SwMATemplateItems` | `PK_SwMATemplateItems` | Items within a SwMA template |
| `SwMATemplateDepartments` | `PK_SwMATemplateDepartments` | Department assignments for SwMA |
| `SwMAs` | — | Actual safety work assessments |
| `SwMAChecks` | `PK_SwMAChecks` (`SwMAChecksId`) | Individual checks within an assessment |
| `SwMACheckType` | — | Check classification |
| `SwMALogs` | — | SwMA event log |
| `SwMARegistrations` | — | SwMA registration records |
| `SwMASAssessors` | — | Assessor assignments |
| `SwMAEventTriggers` | — | Event triggers for SwMA |
| `ResourceSwMACheck` | `PK_ResourceSwMACheck` | Resource-to-check mapping |
| `SwMAJobsAdditionalDefects` | — | Additional defects found during SwMA jobs |
| `SwMAJobsPreExistingDefects` | — | Pre-existing defects noted during SwMA |

### Audits & Inspections
| Table | PK | Notes |
|-------|----|-------|
| `Audits` | — | Audit records |
| `AuditChecks` | `PK_AuditChecks` (`AuditChecksId`) | Individual audit checkpoints |
| `AuditCheckResource` | `PK_AuditCheckResource` | Resource assignments for audit checks |
| `AuditTemporaryTags` | `PK_AuditTemporaryTags` | Temporary tags issued during audits |
| `AuditRFIJobs` | — | RFI jobs linked to audits |
| `AuditRFIIsolations` | — | RFI isolations observed during audits |
| `AuditRFIIsolationSnapshots` | — | Snapshot records for audit RFI isolations |
| `AuditDefects` | — | Defects found during audits |
| `AuditLogs` | — | Audit event log |

### Temporary Tags (Danger Tags / Out-of-Service)
| Table | PK | Notes |
|-------|----|-------|
| `TemporaryTags` | `PK_TemporaryTags` (`TemporaryTagId`) | Active temporary tags |
| `TemporaryTagLogs` | `PK_TemporaryTagLogs` | Tag event history |
| `TemporaryTagState` | — | Tag state tracking |

### Asset Management
| Table | PK | Notes |
|-------|----|-------|
| `Assets` | — | Asset registry |
| `AssetTypes` | `PK_AssetTypes` (`AssetTypeId`) | Asset classification |
| `AssetLogs` | — | Asset event history |
| `Equipment` | — | Equipment registry |
| `EquipmentIsolations` | — | Equipment-to-isolation-point mapping |

### RFI (Request for Information)
| Table | PK | Notes |
|-------|----|-------|
| `RFIs` | — | RFI records |
| `RFIJobs` | `PK_RFIJobs` (`RFIJobId`) | RFI job tracking |
| `RFISystem` | `PK_RFISystem` | RFI-to-system mapping |

### Users, Roles & Permissions
| Table | PK | Notes |
|-------|----|-------|
| `Users` | — | User accounts |
| `UserLogins` | — | Login credentials |
| `UserLoginHistory` | — | Login audit trail |
| `UserRoles` | — | Role assignments |
| `UserPermissions` | — | Permission assignments |
| `UserLogs` | — | User activity log |
| `Groups` | — | Security groups |
| `GroupTypes` | `PK_GroupTypes` (`GroupTypeId`) | Group classification |
| `Roles` | — | Role definitions |
| `Permissions` | — | Permission definitions |

### Workflow & Jobs
| Table | PK | Notes |
|-------|----|-------|
| `Jobs` | — | Job records |
| `JobLogs` | — | Job event history |
| `JobWorkPermitType` | `PK_JobWorkPermitType` | Job-to-permit type mapping |
| `Activities` | — | Activity records |
| `ActivityId` | — | Activity identifier |
| `ReasonCodes` | — | Reason code lookup |

### Messages & Communication
| Table | PK | Notes |
|-------|----|-------|
| `Messages` | — | Message records |
| `MessageTemplates` | `PK_MessageTemplates` | Reusable message templates |
| `MessageType` | — | Message classification |

### Lookup & Configuration
| Table | PK | Notes |
|-------|----|-------|
| `CoordinateSystems` | `PK_CoordinateSystems` | Spatial coordinate systems |
| `BoundaryTemplates` | — | Template definitions |
| `CheckListTemplates` | `PK_CheckListTemplates` | Inspection checklist templates |
| `CheckListTemplateDepartments` | `PK_CheckListTemplateDepartments` | Checklist department assignments |
| `StandardActivity` | — | Standard activity definitions |
| `StandardActivityItems` | — | Items within standard activities |
| `IsolationPointTypes` | — | Isolation point type lookup |

### System Types / Departments Junction
| Table | PK | Notes |
|-------|----|-------|
| `SystemTypesDepartments` | `PK_SystemTypesDepartments` | System type to department mapping |

## Key Relationships

```
Systems
  ├── AreaSystem (1:N) → Areas
  ├── SystemTypes (N:1) → SystemTypes
  │     └── SystemTypesDepartments (1:N) → Departments
  ├── SystemCategories (N:1)
  ├── RFISystem (1:N) → RFIs
  ├── SwMATemplates (1:N) → SwMATemplateDepartments → Departments
  └── IsolationPoints (1:N) → Areas
        ├── IsolationPointChecks (1:N)
        ├── IsolationPointLogs (1:N)
        ├── IsolationPointLockoutDeviceTypes (1:N) → LockoutDeviceTypes
        └── EquipmentIsolations (1:N) → Equipment

Users
  ├── UserLogins (1:N)
  ├── UserRoles (1:N) → Roles
  ├── UserPermissions (1:N) → Permissions
  ├── UserLogs (1:N)
  ├── UserLoginHistory (1:N)
  └── Departments (N:1)

WorkPermits
  ├── JobWorkPermitType (1:N) → Jobs
  ├── WorkPermitTypes (N:1)
  └── Users (ApprovedBy, ReservedBy, ClosureBy)

BoundaryTemplates
  ├── BoundaryTemplateItems (1:N)
  ├── BoundaryTemplateLogs (1:N)
  ├── BoundaryTemplateRFI (1:N) → RFIs
  ├── BoundaryTemplateStandardActivity (1:N) → StandardActivity
  ├── BoundaryTemplateResource (1:N) → Resources
  └── Users (CreatedBy, LastModifiedBy)

SwMAs
  ├── SwMATemplates (N:1)
  ├── SwMAChecks (1:N)
  ├── SwMALogs (1:N)
  ├── SwMASAssessors (1:N) → Users
  ├── SwMAJobsAdditionalDefects (1:N)
  ├── SwMAJobsPreExistingDefects (1:N)
  └── Departments (N:1)
```

## Observation Points (Potential Query Targets)

1. **Which isolation points have the most RFI-linked isolations?** (Safety hotspots)
2. **Which work permit types are most frequently used?** (Workflow patterns)
3. **Audit check failure rates over time** (Compliance trends)
4. **Temporary tag issuance and removal patterns** (Operational tempo)
5. **User login activity by department** (System adoption)
6. **SwMA pass/fail rates by assessor** (Training effectiveness)

## Technical Notes

- **SQL Server 2019** (version 15.x)
- **Collation:** Likely Latin1_General_CI_AS (standard for AU installations)
- **Recovery mode:** Full (based on backup type)
- **Azure AD integrated** (`AzureAD\DarrenIreland` — likely the DBA/admin)
- **Application:** .NET (version 6.0.7 migrations visible in backup: `20230910235550_AddDraftCreatedToBoundaryTemplateItems6.0.7`)
- **Migration history** visible — this is a Code-First EF Core application with 50+ migrations
