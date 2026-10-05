-- clinic_b source schema (MySQL, database clinic_b).
DROP TABLE IF EXISTS Claim;
DROP TABLE IF EXISTS VisitDiagnosis;
DROP TABLE IF EXISTS DxCode;
DROP TABLE IF EXISTS Visit;
DROP TABLE IF EXISTS Patient;

-- Current state only: no history is kept.
CREATE TABLE Patient (
    patientId  varchar(36) PRIMARY KEY,
    firstName  varchar(100),
    lastName   varchar(100),
    dob        date,
    sex        varchar(10),    -- male / female
    ssn        varchar(11),
    street     varchar(200),
    city       varchar(100),
    postalCode varchar(10),
    createdAt  datetime,
    updatedAt  datetime
);

CREATE TABLE Visit (
    visitId    varchar(36) PRIMARY KEY,
    patientId  varchar(36) NOT NULL,
    visitStart datetime,
    visitEnd   datetime,
    visitKind  varchar(30),
    procCode   varchar(20),
    procName   varchar(300),
    totalCost  decimal(14, 2), -- cents before 2023-07-01, currency units after
    isDeleted  tinyint NOT NULL DEFAULT 0
);

-- Local diagnosis codes, translated to SNOMED CT through this dictionary.
CREATE TABLE DxCode (
    localCode  varchar(10) PRIMARY KEY,
    snomedCode varchar(20),
    label      varchar(300)
);

CREATE TABLE VisitDiagnosis (
    visitId   varchar(36) NOT NULL,
    patientId varchar(36) NOT NULL,
    diagDate  date,
    localCode varchar(10)
);

CREATE TABLE Claim (
    claimId     varchar(36) PRIMARY KEY,
    visitId     varchar(36) NOT NULL,
    patientId   varchar(36) NOT NULL,
    serviceDate date,
    amount      decimal(14, 2), -- same unit rule as Visit.totalCost
    claimStatus varchar(10)     -- approved / rejected / pending
);
