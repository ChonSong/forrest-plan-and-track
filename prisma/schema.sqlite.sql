CREATE TABLE IF NOT EXISTS "Equipment" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "SerialNumber" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "AreaId" TEXT NOT NULL,
    "SystemId" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "SerialisedPosition" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "Permissions" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Key" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "IsActive" INTEGER NOT NULL,
    "PermissionGroupId" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "SortOrder" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "RFILogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "RFIId" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "RFILogType" INTEGER NOT NULL,
    "UserId" TEXT NOT NULL,
    "ResourceId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "PriorityExpiry" TEXT NULL,
    "UserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "Jobs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "CompanyId" TEXT NULL,
    "JobNumber" TEXT NULL,
    "NoteNumber" TEXT NULL,
    "Description" TEXT NULL,
    "ReasonCodeId" TEXT NULL,
    "SystemId" TEXT NULL,
    "StandardActivityId" TEXT NULL,
    "PlannedStartDate" TEXT NULL,
    "PlannedEndDate" TEXT NULL,
    "InternalTask" INTEGER NOT NULL,
    "JobState" INTEGER NOT NULL,
    "SetToWorkRequired" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "ActivityId" TEXT NULL,
    "GroupId" TEXT NULL,
    "DepartmentId" TEXT NULL,
    "ControlledJob" INTEGER NOT NULL,
    "OnHold" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "AuditRFIIsolationSnapshots" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "AuditId" TEXT NOT NULL,
    "RFIIsolationId" TEXT NOT NULL,
    "ResourceId" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "IsolationPointIsolationPoint" (
    "IsolationPointId" TEXT,
    "ParentIsolationPointId" TEXT,
    PRIMARY KEY ("IsolationPointId", "ParentIsolationPointId")
);

CREATE TABLE IF NOT EXISTS "SwMALogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "SwMAId" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "SwMALogType" INTEGER NOT NULL,
    "UserId" TEXT NOT NULL,
    "ResourceId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "DateTimeCompleted" TEXT NOT NULL,
    "DateTimeStarted" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "Messages" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "UserId" TEXT NULL,
    "SenderUserId" TEXT NULL,
    "SourceMessageId" TEXT NULL,
    "MessageNote" TEXT NULL,
    "AssociatedTableId" TEXT NULL,
    "AssociatedTable" INTEGER NOT NULL,
    "MessageType" INTEGER NOT NULL,
    "MessageStatus" INTEGER NOT NULL,
    "BroadcastStart" TEXT NULL,
    "BroadcastEnd" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "CheckListTemplates" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Version" TEXT NOT NULL,
    "GroupId" TEXT NOT NULL,
    "CheckListTemplateTypeId" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "SwMANumber" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "ReasonCodes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Code" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "Internal" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "AuditRFIs" (
    "AuditsId" TEXT,
    "RFIsId" TEXT,
    PRIMARY KEY ("AuditsId", "RFIsId")
);

CREATE TABLE IF NOT EXISTS "AuditDefects" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "AuditId" TEXT NOT NULL,
    "IsolationPointId" TEXT NOT NULL,
    "DefectDescription" TEXT NOT NULL,
    "AuditDefectDate" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "WorkPermits" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "WorkPermitTypeId" TEXT NOT NULL,
    "RFIId" TEXT NULL,
    "JobId" TEXT NULL,
    "UserId" TEXT NULL,
    "Description" TEXT NOT NULL,
    "AcknowledgedBySignatureId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "UserSnapshot" TEXT NOT NULL,
    "AcknowledgedById" TEXT NULL,
    "AcknowledgedBySnapshot" TEXT NULL,
    "AcknowledgedDate" TEXT NULL,
    "AcknowledgedComment" TEXT NULL,
    "ClosureUserId" TEXT NULL,
    "ClosureComment" TEXT NULL,
    "ClosureDate" TEXT NULL,
    "ClosureSignatureId" TEXT NULL,
    "ClosureUserSnapshot" TEXT NULL,
    "State" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "EventLogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "UserId" TEXT NULL,
    "EventLogArea" TEXT NOT NULL,
    "EventLogOperations" INTEGER NOT NULL,
    "ObjectId" TEXT NOT NULL,
    "Description" TEXT NULL,
    "CreatedDate" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "RFIIsolationResource" (
    "IsolationsId" TEXT,
    "ResourcesId" TEXT,
    PRIMARY KEY ("IsolationsId", "ResourcesId")
);

CREATE TABLE IF NOT EXISTS "RFIJobs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "RFIId" TEXT NOT NULL,
    "JobId" TEXT NOT NULL,
    "LinkingUserId" TEXT NULL,
    "LinkingSignatureId" TEXT NULL,
    "LinkingDate" TEXT NOT NULL,
    "DeLinkingUserId" TEXT NULL,
    "DeLinkingSignatureId" TEXT NULL,
    "DeLinkingDate" TEXT NOT NULL,
    "SetToWorkDate" TEXT NOT NULL,
    "SetToWorkCompleteSignatureId" TEXT NULL,
    "SetToWorkCompleteDate" TEXT NOT NULL,
    "WorkCompleteDate" TEXT NOT NULL,
    "WorkCompleteSignatureId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "PercentageComplete" INTEGER NOT NULL,
    "DeLinkingUserSnapshot" TEXT NOT NULL,
    "LinkingUserSnapshot" TEXT NOT NULL,
    "RFIJobState" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "SwMAChecks" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "SwMAId" TEXT NOT NULL,
    "CheckListTemplateItemId" TEXT NOT NULL,
    "Index" INTEGER NOT NULL,
    "SwMACheckType" INTEGER NOT NULL,
    "AssessorId" TEXT NOT NULL,
    "Note" TEXT NOT NULL,
    "EnergyRecordedValue" REAL NOT NULL,
    "EnergyRecordedType" INTEGER NOT NULL,
    "DefectFound" INTEGER NOT NULL,
    "DefectDescription" TEXT NOT NULL,
    "CheckListTemplateItemError" INTEGER NOT NULL,
    "CheckListTemplateItemDesc" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Completed" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "Activities" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "GroupVesselId" TEXT NOT NULL,
    "Number" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "Active" INTEGER NOT NULL,
    "ActivityStartDate" TEXT NOT NULL,
    "ActivityEndDate" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "UserLoginHistory" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "UserId" TEXT NOT NULL,
    "LoginTime" TEXT NOT NULL,
    "LogoutTime" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "SessionId" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "WorkPermitTypes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Prefix" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "TemporaryTagLogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "TemporaryTagId" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "TemporaryTagLogType" INTEGER NOT NULL,
    "UserId" TEXT NOT NULL,
    "ResourceId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "UserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "SwMATemplates" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Version" TEXT NOT NULL,
    "SwMATemplateType" INTEGER NOT NULL,
    "AreaId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "SystemId" TEXT NULL,
    "SwMANumber" TEXT NOT NULL,
    "GroupId" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "IsolationPointLogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "IsolationPointId" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "IsolationPointLogType" INTEGER NOT NULL,
    "UserId" TEXT NOT NULL,
    "ResourceId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Comment" TEXT NOT NULL,
    "UserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "PadLocks" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "SerialNumber" TEXT NOT NULL,
    "PadLockTypeId" TEXT NOT NULL,
    "UserId" TEXT NULL,
    "TrackingEnabled" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Active" INTEGER NOT NULL,
    "DeactivatedBy" TEXT NULL,
    "DeactivatedDate" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "SystemTypesDepartments" (
    "DepartmentsId" TEXT,
    "SystemTypesId" TEXT,
    PRIMARY KEY ("DepartmentsId", "SystemTypesId")
);

CREATE TABLE IF NOT EXISTS "LockoutDevices" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "SerialNumber" TEXT NOT NULL,
    "LockoutDeviceTypeId" TEXT NOT NULL,
    "UserId" TEXT NULL,
    "TrackingEnabled" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "ResourceSwMA" (
    "ResourcesId" TEXT,
    "SwMAsId" TEXT,
    PRIMARY KEY ("ResourcesId", "SwMAsId")
);

CREATE TABLE IF NOT EXISTS "SwMATemplateDepartments" (
    "DepartmentsId" TEXT,
    "SwMATemplatesId" TEXT,
    PRIMARY KEY ("DepartmentsId", "SwMATemplatesId")
);

CREATE TABLE IF NOT EXISTS "Systems" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "ParentId" TEXT NULL,
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Code" TEXT NOT NULL,
    "SystemTypeId" TEXT NOT NULL,
    "SystemCategoryId" TEXT NOT NULL,
    "DepartmentId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "AuditChecks" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "AuditId" TEXT NOT NULL,
    "RFIIsolationId" TEXT NULL,
    "RFIJobId" TEXT NULL,
    "AuditCheckType" INTEGER NOT NULL,
    "DefectFound" INTEGER NOT NULL,
    "DefectDescription" TEXT NOT NULL,
    "ActionsTaken" INTEGER NOT NULL,
    "ActionsDescription" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "TemporaryTagId" TEXT NULL,
    "CheckQuestion" TEXT NOT NULL,
    "RFIId" TEXT NULL,
    "AuditCheckDate" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "AuditTemporaryTags" (
    "AuditsId" TEXT,
    "TemporaryTagsId" TEXT,
    PRIMARY KEY ("AuditsId", "TemporaryTagsId")
);

CREATE TABLE IF NOT EXISTS "IsolationPoints" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "IsolationPointStatus" INTEGER NOT NULL,
    "Name" TEXT NOT NULL,
    "FLOC" TEXT NOT NULL,
    "TallyPlate" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "DeactiveState" INTEGER NOT NULL,
    "ActiveState" INTEGER NOT NULL,
    "CurrentState" INTEGER NOT NULL,
    "IsolationPointTypeId" TEXT NOT NULL,
    "AreaId" TEXT NOT NULL,
    "SubAreaId" TEXT NULL,
    "CriticalSystem" INTEGER NOT NULL,
    "HighRiskPlant" INTEGER NOT NULL,
    "Lockable" INTEGER NOT NULL,
    "PreferredPadLockTypeId" TEXT NULL,
    "ValidationPossible" INTEGER NOT NULL,
    "ValidationMethod" TEXT NOT NULL,
    "EnergyPotentialValue" REAL NOT NULL,
    "EnergyPotentialType" INTEGER NOT NULL,
    "EnergyPotentialSubValue" REAL NOT NULL,
    "EnergyPotentialSubValueType" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "SerialisedPosition" TEXT NOT NULL,
    "SystemId" TEXT NULL,
    "UID" TEXT NOT NULL,
    "DeactivatedBy" TEXT NULL,
    "DeactivatedDate" TEXT NULL,
    "DefectReported" INTEGER NOT NULL,
    "Version" TEXT NOT NULL,
    "DefectDescription" TEXT NOT NULL,
    "EnergyPotential" TEXT NOT NULL,
    "OneTagDisplayName" TEXT NOT NULL,
    "SufficientIsolation" INTEGER NOT NULL,
    "AlternateLockoutDeviceTypeId" TEXT NULL,
    "PreferredLockoutDeviceTypeId" TEXT NULL,
    "CreatorUserId" TEXT NOT NULL,
    "CreatorUserSnapshot" TEXT NOT NULL,
    "LastModifiedUserId" TEXT NOT NULL,
    "LastModifiedUserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "Resources" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "ResourceType" INTEGER NOT NULL,
    "Description" TEXT NOT NULL,
    "ResourceData" BLOB NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "MediaType" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "ResourceAllocation" INTEGER NULL,
    "ResourcePath" TEXT NOT NULL,
    "FileExtension" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "SwMARegisters" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "GroupClassId" TEXT NOT NULL,
    "GroupVesselId" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "EventStartDate" TEXT NOT NULL,
    "EventEndDate" TEXT NOT NULL,
    "SwMACoordinatorId" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Active" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "Users" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "FirstName" TEXT NOT NULL,
    "LastName" TEXT NOT NULL,
    "UserName" TEXT NOT NULL,
    "Mobile" TEXT NOT NULL,
    "Email" TEXT NOT NULL,
    "Address" TEXT NOT NULL,
    "BadgeSerialNumber" TEXT NOT NULL,
    "Position" TEXT NOT NULL,
    "Permissions" REAL NOT NULL,
    "GroupId" TEXT NULL,
    "UserRoleId" TEXT NOT NULL,
    "DepartmentId" TEXT NULL,
    "UserLoginId" TEXT NULL,
    "CompanyId" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Competencies" REAL NOT NULL,
    "ProfileImage" BLOB NULL,
    "Signature" BLOB NULL,
    "DeactivatedBy" TEXT NULL,
    "DeactivatedDate" TEXT NULL,
    "AccountLocked" INTEGER NOT NULL,
    "AccountLockedDate" TEXT NULL,
    "LoginAttempts" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "LockoutDeviceTypes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Colour" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "TotalCount" REAL NOT NULL,
    "TotalInUse" REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS "Lockboxes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "SerialNumber" TEXT NOT NULL,
    "RFIId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "DeactivatedBy" TEXT NULL,
    "DeactivatedDate" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "DangerTag" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "TagNumber" TEXT NOT NULL,
    "SerialNumber" TEXT NOT NULL,
    "TrackingEnabled" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "PrintCount" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "BoundaryTemplateLogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "BoundaryTemplateId" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "BoundaryTemplateLogType" INTEGER NOT NULL,
    "UserId" TEXT NOT NULL,
    "UserSnapshot" TEXT NOT NULL,
    "ResourceId" TEXT NULL,
    "PriorityExpiry" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "Maps" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "ResourceId" TEXT NOT NULL,
    "SerialisedOrigin" TEXT NOT NULL,
    "SerialisedScale" TEXT NOT NULL,
    "SerialisedBounds" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "MessageTemplates" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "MessageNote" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "StandardActivitySystem" (
    "StandardActivitesId" TEXT,
    "SystemsId" TEXT,
    PRIMARY KEY ("StandardActivitesId", "SystemsId")
);

CREATE TABLE IF NOT EXISTS "AssetLogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "AssetTypeId" TEXT NOT NULL,
    "UserId" TEXT NOT NULL,
    "ChangeAmount" REAL NOT NULL,
    "Comment" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "Departments" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "ParentDepartmentId" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "UserRolePermissions" (
    "UserRoleId" TEXT,
    "PermissionId" TEXT,
    PRIMARY KEY ("UserRoleId", "PermissionId")
);

CREATE TABLE IF NOT EXISTS "RFILockBoxes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "RFIId" TEXT NOT NULL,
    "SerialNumber" TEXT NOT NULL,
    "UserId" TEXT NOT NULL,
    "PadLockId" TEXT NOT NULL,
    "LockBoxAreaId" TEXT NOT NULL,
    "PadLockAreaId" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "LockboxId" TEXT NOT NULL,
    "VerificationLockId" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "JobResource" (
    "JobsId" TEXT,
    "ResourcesId" TEXT,
    PRIMARY KEY ("JobsId", "ResourcesId")
);

CREATE TABLE IF NOT EXISTS "ResourceSwMACheck" (
    "ResourcesId" TEXT,
    "SwMAChecksId" TEXT,
    PRIMARY KEY ("ResourcesId", "SwMAChecksId")
);

CREATE TABLE IF NOT EXISTS "JobWorkPermitType" (
    "JobId" TEXT,
    "WorkPermitTypeId" TEXT,
    PRIMARY KEY ("JobId", "WorkPermitTypeId")
);

CREATE TABLE IF NOT EXISTS "BoundaryTemplates" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "BoundaryTemplateType" INTEGER NOT NULL,
    "UserId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Version" TEXT NOT NULL,
    "OnHold" INTEGER NOT NULL,
    "CreatorUserId" TEXT NOT NULL,
    "CreatorUserSnapshot" TEXT NOT NULL,
    "DeactivatedBy" TEXT NULL,
    "DeactivatedDate" TEXT NULL,
    "LastModifiedUserId" TEXT NOT NULL,
    "LastModifiedUserSnapshot" TEXT NOT NULL,
    "Imported" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "IsolationPointTypes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "IsolationType" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "SwMAJobsAdditionalDefects" (
    "AdditionalDefectsId" TEXT,
    "SwMAAdditionalDefectsId" TEXT,
    PRIMARY KEY ("AdditionalDefectsId", "SwMAAdditionalDefectsId")
);

CREATE TABLE IF NOT EXISTS "RFIs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Description" TEXT NOT NULL,
    "RFINumber" TEXT NOT NULL,
    "RFIState" INTEGER NOT NULL,
    "GroupId" TEXT NULL,
    "DeveloperUserId" TEXT NOT NULL,
    "IsolationUserId" TEXT NULL,
    "RFILockBoxId" TEXT NULL,
    "ReservedUserId" TEXT NULL,
    "ExpectedStartDate" TEXT NOT NULL,
    "ExpectedEndDate" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "AlteredState" INTEGER NOT NULL,
    "Immediate" INTEGER NOT NULL,
    "LockedUserId" TEXT NULL,
    "ActivityId" TEXT NULL,
    "Simple" INTEGER NOT NULL,
    "RequestedUserId" TEXT NULL,
    "DeveloperUserSnapshot" TEXT NOT NULL,
    "IsolationUserSnapshot" TEXT NOT NULL,
    "LockedUserSnapshot" TEXT NOT NULL,
    "RequestedUserSnapshot" TEXT NOT NULL,
    "ReservedUserSnapshot" TEXT NOT NULL,
    "VerificationRequired" INTEGER NOT NULL,
    "CreatorUserId" TEXT NOT NULL,
    "CreatorUserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "BoundaryTemplateItems" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "BoundaryTemplateId" TEXT NOT NULL,
    "Index" INTEGER NOT NULL,
    "Comment" TEXT NOT NULL,
    "IsolationPointId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "AppliedState" INTEGER NOT NULL,
    "EquipmentId" TEXT NULL,
    "HoldPoint" INTEGER NOT NULL,
    "DraftCreated" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "CoordinateSystems" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "SerialisedBounds" TEXT NOT NULL,
    "SerialisedOrigin" TEXT NOT NULL,
    "Rotation" REAL NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "AreaSystem" (
    "AreasId" TEXT,
    "SystemsId" TEXT,
    PRIMARY KEY ("AreasId", "SystemsId")
);

CREATE TABLE IF NOT EXISTS "Zones" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "ZoneType" INTEGER NOT NULL,
    "SerialisedBounds" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "StandardActivityItems" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "StandardActivityId" TEXT NOT NULL,
    "Index" INTEGER NOT NULL,
    "Comment" TEXT NOT NULL,
    "StandardActivityItemType" INTEGER NOT NULL,
    "IsolationPointId" TEXT NULL,
    "EquipmentId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "RFILockResource" (
    "RFILocksId" TEXT,
    "ResourcesId" TEXT,
    PRIMARY KEY ("RFILocksId", "ResourcesId")
);

CREATE TABLE IF NOT EXISTS "Groups" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "ParentId" TEXT NULL,
    "GroupTypeId" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Code" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "CoordinateSystemId" TEXT NULL,
    "MapId" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "RFILocksRFIJobs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "RFILockId" TEXT NOT NULL,
    "RFIJobId" TEXT NOT NULL,
    "RFILockState" INTEGER NOT NULL,
    "LockOnSignatureId" TEXT NULL,
    "LockOnDate" TEXT NOT NULL,
    "LockOnComment" TEXT NOT NULL,
    "LockOffSignatureId" TEXT NULL,
    "LockOffDate" TEXT NOT NULL,
    "LockOffComment" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "PercentageComplete" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "RFIAreas" (
    "AreasId" TEXT,
    "RFIsId" TEXT,
    PRIMARY KEY ("AreasId", "RFIsId")
);

CREATE TABLE IF NOT EXISTS "SystemCategories" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Colour" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "EventLogTransactions" (
    "Id" INTEGER PRIMARY KEY,
    "EventLogId" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "IsolationPointResource" (
    "IsolationPointsId" TEXT,
    "ResourcesId" TEXT,
    PRIMARY KEY ("IsolationPointsId", "ResourcesId")
);

CREATE TABLE IF NOT EXISTS "CheckListTemplateTypes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "BoundaryTemplateResource" (
    "BoundaryTemplatesId" TEXT,
    "ResourcesId" TEXT,
    PRIMARY KEY ("BoundaryTemplatesId", "ResourcesId")
);

CREATE TABLE IF NOT EXISTS "Audits" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "AuditType" INTEGER NOT NULL,
    "AuditState" INTEGER NOT NULL,
    "EventStartDate" TEXT NOT NULL,
    "EventEndDate" TEXT NOT NULL,
    "ActivityId" TEXT NULL,
    "ReservedUserId" TEXT NULL,
    "DateCompleted" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Defects" INTEGER NOT NULL,
    "DateApproved" TEXT NULL,
    "ApprovedUserId" TEXT NULL,
    "ApprovedUserSnapshot" TEXT NOT NULL,
    "ReservedUserSnapshot" TEXT NOT NULL,
    "DateSignOff" TEXT NULL,
    "SignOffUserId" TEXT NULL,
    "SignOffUserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "SwMAs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "SwMARegisterId" TEXT NOT NULL,
    "SwMATemplateId" TEXT NOT NULL,
    "SwMAEventTrigger" INTEGER NOT NULL,
    "SwMANumber" TEXT NOT NULL,
    "SwMAState" INTEGER NOT NULL,
    "Defects" INTEGER NOT NULL,
    "HRAStatus" INTEGER NOT NULL,
    "SwMACoordinatorId" TEXT NULL,
    "SupervisorId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "DepartmentId" TEXT NOT NULL,
    "ReservedUserId" TEXT NULL,
    "ActualTotalMins" INTEGER NOT NULL,
    "QuotedTotalMins" INTEGER NOT NULL,
    "CompletedDate" TEXT NULL,
    "DeferredDate" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "AreaTypes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "SecureArea" INTEGER NOT NULL,
    "HighRisk" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "EquipmentIsolations" (
    "EquipmentId" TEXT,
    "IsolationPointId" TEXT,
    "Id" TEXT NOT NULL,
    "Notes" TEXT NOT NULL,
    "Secondary" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    PRIMARY KEY ("EquipmentId", "IsolationPointId")
);

CREATE TABLE IF NOT EXISTS "AuditCheckResource" (
    "AuditChecksId" TEXT,
    "ResourcesId" TEXT,
    PRIMARY KEY ("AuditChecksId", "ResourcesId")
);

CREATE TABLE IF NOT EXISTS "AuditRFIJobs" (
    "AuditsId" TEXT,
    "RFIJobsId" TEXT,
    PRIMARY KEY ("AuditsId", "RFIJobsId")
);

CREATE TABLE IF NOT EXISTS "RFILocks" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "RFIId" TEXT NOT NULL,
    "UserId" TEXT NOT NULL,
    "PadLockId" TEXT NOT NULL,
    "RFILockState" INTEGER NOT NULL,
    "LockOnSignatureId" TEXT NULL,
    "LockOnDate" TEXT NOT NULL,
    "LockOffSignatureId" TEXT NULL,
    "LockOffDate" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "LockOnComment" TEXT NOT NULL,
    "LockOffComment" TEXT NOT NULL,
    "UserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "GroupTypes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "TemporaryTags" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "RFIId" TEXT NULL,
    "IsolationPointId" TEXT NULL,
    "EquipmentId" TEXT NULL,
    "TemporaryTagState" INTEGER NOT NULL,
    "Notes" TEXT NOT NULL,
    "TemporaryTagNumber" TEXT NOT NULL,
    "AppliedUserId" TEXT NULL,
    "AppliedSignatureId" TEXT NULL,
    "AppliedDate" TEXT NOT NULL,
    "RemovalUserId" TEXT NULL,
    "RemovalSignatureId" TEXT NULL,
    "RemovalDate" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "AppliedState" INTEGER NOT NULL,
    "AppliedUserSnapshot" TEXT NOT NULL,
    "RemovalUserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "BoundaryTemplateSystem" (
    "BoundaryTemplatesId" TEXT,
    "SystemsId" TEXT,
    PRIMARY KEY ("BoundaryTemplatesId", "SystemsId")
);

CREATE TABLE IF NOT EXISTS "Companies" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Phone" TEXT NOT NULL,
    "Email" TEXT NOT NULL,
    "ContactPerson" TEXT NOT NULL,
    "Address" TEXT NOT NULL,
    "GroupId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Code" TEXT NOT NULL,
    "DeactivatedBy" TEXT NULL,
    "DeactivatedDate" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "CheckListTemplateDepartments" (
    "CheckListTemplatesId" TEXT,
    "DepartmentsId" TEXT,
    PRIMARY KEY ("CheckListTemplatesId", "DepartmentsId")
);

CREATE TABLE IF NOT EXISTS "Areas" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Code" TEXT NOT NULL,
    "GroupId" TEXT NOT NULL,
    "AreaTypeId" TEXT NOT NULL,
    "DepartmentId" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "SerialisedBounds" TEXT NOT NULL,
    "SerialisedOrigin" TEXT NOT NULL,
    "ParentAreaId" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "AuditRFIIsolations" (
    "AuditsId" TEXT,
    "RFIIsolationsId" TEXT,
    PRIMARY KEY ("AuditsId", "RFIIsolationsId")
);

CREATE TABLE IF NOT EXISTS "JobLogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "JobId" TEXT NOT NULL,
    "JobLogType" INTEGER NOT NULL,
    "Description" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "UserId" TEXT NOT NULL,
    "UserSnapshot" TEXT NOT NULL,
    "ResourceId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "BoundaryTemplateStandardActivity" (
    "BoundaryTemplatesId" TEXT,
    "StandardActivitiesId" TEXT,
    PRIMARY KEY ("BoundaryTemplatesId", "StandardActivitiesId")
);

CREATE TABLE IF NOT EXISTS "UserLogins" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "LastLogin" TEXT NOT NULL,
    "LastPasswordChange" TEXT NOT NULL,
    "PasswordSalt" BLOB NOT NULL,
    "PasswordHash" BLOB NOT NULL,
    "LastPasswordSalt" BLOB NULL,
    "LastPasswordHash" BLOB NULL,
    "UserLoginStates" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "SwMAJobsPreExistingDefects" (
    "PreExistingDefectsId" TEXT,
    "SwMAExistingDefectsId" TEXT,
    PRIMARY KEY ("PreExistingDefectsId", "SwMAExistingDefectsId")
);

CREATE TABLE IF NOT EXISTS "StandardActivities" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "StandardActivityNumber" TEXT NOT NULL,
    "DocumentNumber" TEXT NOT NULL,
    "SetToWorkRequired" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "Description" TEXT NOT NULL,
    "FacilityCode" TEXT NOT NULL,
    "RevisionDate" TEXT NOT NULL,
    "RevisionNumber" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "RFISystem" (
    "RFIsId" TEXT,
    "SystemsId" TEXT,
    PRIMARY KEY ("RFIsId", "SystemsId")
);

CREATE TABLE IF NOT EXISTS "UserRoles" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Permissions" REAL NOT NULL,
    "RoleLevel" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "DeactivatedBy" TEXT NULL,
    "DeactivatedDate" TEXT NULL,
    "ReadOnly" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "AuditLogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "AuditId" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "AuditLogType" INTEGER NOT NULL,
    "UserId" TEXT NOT NULL,
    "ResourceId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "PriorityExpiry" TEXT NULL,
    "UserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "PermissionGroups" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "IsSystem" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "SortOrder" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "CheckListTemplateItems" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Version" TEXT NOT NULL,
    "Instruction" TEXT NOT NULL,
    "CheckListTemplateItemType" INTEGER NOT NULL,
    "CheckListTemplateId" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "EquipmentId" TEXT NULL,
    "IsolationPointId" TEXT NULL,
    "EnergyNominalType" INTEGER NOT NULL,
    "EnergyNominalValue" REAL NOT NULL,
    "SwMATable" INTEGER NOT NULL,
    "TimeInMins" INTEGER NOT NULL,
    "Index" INTEGER NOT NULL,
    "ResourceId" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "SwMASAssessors" (
    "AssessorsId" TEXT,
    "SwMASId" TEXT,
    PRIMARY KEY ("AssessorsId", "SwMASId")
);

CREATE TABLE IF NOT EXISTS "UserLogs" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "UserId" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Comment" TEXT NOT NULL,
    "UserLogType" INTEGER NOT NULL,
    "LogAuthorUserId" TEXT NOT NULL,
    "ResourceId" TEXT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "LogAuthorUserSnapshot" TEXT NOT NULL,
    "UserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "AssetTypes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Flags" REAL NOT NULL,
    "TotalCount" REAL NOT NULL,
    "TotalInUse" REAL NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "ResourceWorkPermit" (
    "ResourcesId" TEXT,
    "WorkPermitsId" TEXT,
    PRIMARY KEY ("ResourcesId", "WorkPermitsId")
);

CREATE TABLE IF NOT EXISTS "BoundaryTemplateRFI" (
    "BoundaryTemplatesId" TEXT,
    "RFIsId" TEXT,
    PRIMARY KEY ("BoundaryTemplatesId", "RFIsId")
);

CREATE TABLE IF NOT EXISTS "RFIResource" (
    "RFIsId" TEXT,
    "ResourcesId" TEXT,
    PRIMARY KEY ("RFIsId", "ResourcesId")
);

CREATE TABLE IF NOT EXISTS "RFIIsolations" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "RFIId" TEXT NOT NULL,
    "IsolationPointId" TEXT NULL,
    "DangerTagId" TEXT NULL,
    "PadLockId" TEXT NULL,
    "LockOutDeviceId" TEXT NULL,
    "EquipmentId" TEXT NULL,
    "RFIIsolationState" INTEGER NOT NULL,
    "Description" TEXT NOT NULL,
    "AppliedState" INTEGER NOT NULL,
    "AppliedUserId" TEXT NULL,
    "AppliedSignatureId" TEXT NULL,
    "AppliedDate" TEXT NOT NULL,
    "RemovalState" INTEGER NOT NULL,
    "RemovalUserId" TEXT NULL,
    "RemovalSignatureId" TEXT NULL,
    "RemovalDate" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "HighRisk" INTEGER NOT NULL,
    "HoldPoint" INTEGER NOT NULL,
    "Index" INTEGER NOT NULL,
    "Printed" INTEGER NOT NULL,
    "PrintedUserId" TEXT NULL,
    "ReservedUserId" TEXT NULL,
    "LockOutDeviceTypeId" TEXT NULL,
    "RFILockBoxId" TEXT NULL,
    "LastAuditId" TEXT NULL,
    "AppliedUserSnapshot" TEXT NOT NULL,
    "PrintedUserSnapshot" TEXT NOT NULL,
    "RemovalUserSnapshot" TEXT NOT NULL,
    "ReservedUserSnapshot" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "IsolationPointChecks" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "IsolationPointTypeId" TEXT NULL,
    "IsolationPointId" TEXT NULL,
    "Name" TEXT NOT NULL,
    "Mandatory" INTEGER NOT NULL,
    "Order" INTEGER NOT NULL,
    "DisplayText" TEXT NOT NULL,
    "BooleanType" INTEGER NOT NULL,
    "DefaultValue" TEXT NOT NULL,
    "IsolationPointStates" INTEGER NOT NULL,
    "MovingToStates" INTEGER NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "PadLockTypes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Colour" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL,
    "PersonalLock" INTEGER NOT NULL,
    "VerificationLock" INTEGER NOT NULL,
    "DeactivatedBy" TEXT NULL,
    "DeactivatedDate" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "SwMATemplateItems" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Index" INTEGER NOT NULL,
    "SwMATemplateId" TEXT NOT NULL,
    "CheckListTemplateItemId" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

CREATE TABLE IF NOT EXISTS "UserPermissions" (
    "UserId" TEXT,
    "PermissionId" TEXT,
    "Override" INTEGER NOT NULL,
    PRIMARY KEY ("UserId", "PermissionId")
);

CREATE TABLE IF NOT EXISTS "SystemTypes" (
    "Id" TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    "Name" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Colour" TEXT NOT NULL,
    "CreatedDate" TEXT NOT NULL,
    "ModifiedDate" TEXT NULL,
    "DeletedDate" TEXT NULL,
    "CreatedBy" TEXT NOT NULL,
    "ModifiedBy" TEXT NULL,
    "DeletedBy" TEXT NULL
);

