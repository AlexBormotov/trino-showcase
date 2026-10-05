-- Runs once, on an empty data volume.
CREATE DATABASE clinic_a;
CREATE DATABASE polaris;

\connect polaris
-- Polaris does not create its own schema.
CREATE SCHEMA IF NOT EXISTS polaris_schema;
