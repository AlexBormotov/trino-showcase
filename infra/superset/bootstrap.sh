#!/bin/sh
# Prepare the metadata database and users, then start the server. Safe to rerun.
set -e
superset db upgrade
superset fab create-admin --username admin --firstname Admin --lastname Demo \
  --email admin@example.com --password admin 2>/dev/null || true
superset init
# Analysts get Superset's Alpha role (see every dataset); which rows and columns they
# see is decided by Trino, because the database connection impersonates the logged-in user.
for user in tenant_a_analyst cross_tenant_analyst; do
  superset fab create-user --role Alpha --username "$user" --firstname "$user" --lastname Demo \
    --email "$user@example.com" --password "$user" 2>/dev/null || true
done
exec /usr/bin/run-server.sh
