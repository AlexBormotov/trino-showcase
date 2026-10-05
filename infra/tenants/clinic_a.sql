-- clinic_a source schema (PostgreSQL). app_v1 holds activity before 2024-01-01,
-- app_v2 holds activity from then on. Patients exist only in app_v2.
DROP SCHEMA IF EXISTS app_v1 CASCADE;
DROP SCHEMA IF EXISTS app_v2 CASCADE;
CREATE SCHEMA app_v1;
CREATE SCHEMA app_v2;

CREATE TABLE app_v1.visit (
    visit_id    text PRIMARY KEY,
    pat_id      text NOT NULL,
    visit_date  varchar(19),   -- DD.MM.YYYY HH24:MI:SS
    end_date    varchar(19),
    visit_type  text,
    reason_code text,
    reason_text text,
    cost        numeric(12, 2)
);

CREATE TABLE app_v1.dx (
    pat_id      text NOT NULL,
    visit_id    text NOT NULL,
    dx_date     varchar(10),   -- DD.MM.YYYY
    snomed_code text,
    dx_text     text
);

CREATE TABLE app_v1.bill (
    bill_id   text PRIMARY KEY,
    visit_id  text NOT NULL,
    pat_id    text NOT NULL,
    bill_date varchar(10),     -- DD.MM.YYYY
    amount    numeric(12, 2),
    state     char(1)          -- P paid, D denied, O open
);

CREATE TABLE app_v2.patients (
    patient_id text PRIMARY KEY,
    first_name text,
    last_name  text,
    birth_date date,
    gender     varchar(1),     -- M/F, or 1/2 for patients registered before 2024
    ssn        text,
    address    text,
    city       text,
    zip        text,
    updated_at timestamp
);

-- Change log of patient addresses: one I row per patient, U rows for moves.
CREATE TABLE app_v2.patient_cdc (
    lsn        bigint PRIMARY KEY,
    op         char(1),
    changed_at timestamp,
    patient_id text,
    address    text,
    city       text,
    zip        text
);

CREATE TABLE app_v2.encounters (
    encounter_id    text PRIMARY KEY,
    patient_id      text NOT NULL,
    started_at      timestamp,
    ended_at        timestamp,
    encounter_class text,
    snomed_code     text,
    description     text,
    total_cost      numeric(12, 2)
);

CREATE TABLE app_v2.diagnoses (
    encounter_id text NOT NULL,
    patient_id   text NOT NULL,
    diagnosed_on date,
    code         text,
    description  text
);

CREATE TABLE app_v2.claims (
    claim_id     text PRIMARY KEY,
    encounter_id text NOT NULL,
    patient_id   text NOT NULL,
    service_date date,
    amount       numeric(12, 2),
    status       text          -- PAID, DENIED, PENDING
);
