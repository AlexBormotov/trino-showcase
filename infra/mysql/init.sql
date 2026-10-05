-- Runs once, on an empty data volume (database clinic_b is created by MYSQL_DATABASE).

-- Trino reads tenant data as this user: SELECT on clinic_b only.
CREATE USER 'trino_reader'@'%' IDENTIFIED BY 'trino_reader';
GRANT SELECT ON clinic_b.* TO 'trino_reader'@'%';

-- Trino's audit event listener writes here; the audit catalog reads it.
CREATE DATABASE trino_audit;
CREATE USER 'trino_audit'@'%' IDENTIFIED BY 'trino_audit';
GRANT ALL ON trino_audit.* TO 'trino_audit'@'%';
CREATE USER 'audit_reader'@'%' IDENTIFIED BY 'audit_reader';
GRANT SELECT ON trino_audit.* TO 'audit_reader'@'%';
