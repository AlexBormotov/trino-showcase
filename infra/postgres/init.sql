-- Runs once, on an empty data volume.
CREATE DATABASE clinic_a;
CREATE DATABASE polaris;

-- Trino reads tenant data as this role; schema grants are applied by infra/tenants/clinic_a.sql.
CREATE ROLE trino_reader LOGIN PASSWORD 'trino_reader';
GRANT CONNECT ON DATABASE clinic_a TO trino_reader;

\connect polaris
-- Polaris does not create its own schema.
CREATE SCHEMA IF NOT EXISTS polaris_schema;
