#!/bin/sh
# Creates the Iceberg catalog "lake" in Polaris, backed by s3://warehouse on RustFS.
# Idempotent: an existing catalog is left as it is.
set -eu

POLARIS=http://polaris:8181
REALM=POLARIS

TOKEN=$(curl -sf "$POLARIS/api/catalog/v1/oauth/tokens" \
  -H "Polaris-Realm: $REALM" \
  --user root:s3cr3t \
  -d grant_type=client_credentials \
  -d scope=PRINCIPAL_ROLE:ALL | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
[ -n "$TOKEN" ] || { echo "no access token" >&2; exit 1; }

api() {
  curl -sf -H "Authorization: Bearer $TOKEN" -H "Polaris-Realm: $REALM" \
    -H 'Content-Type: application/json' "$@"
}

if api "$POLARIS/api/management/v1/catalogs/lake" >/dev/null 2>&1; then
  echo "catalog lake exists"
else
  api -X POST "$POLARIS/api/management/v1/catalogs" -d '{
    "catalog": {
      "name": "lake",
      "type": "INTERNAL",
      "properties": {
        "default-base-location": "s3://warehouse/lake",
        "polaris.config.drop-with-purge.enabled": "true"
      },
      "storageConfigInfo": {
        "storageType": "S3",
        "allowedLocations": ["s3://warehouse/lake"],
        "endpoint": "http://localhost:19000",
        "endpointInternal": "http://rustfs:9000",
        "pathStyleAccess": true,
        "region": "us-west-2"
      }
    }
  }'
  echo "catalog lake created"
fi

# catalog_admin is granted to the root principal's role by default; it also needs
# content privileges to create namespaces and tables.
api -X PUT "$POLARIS/api/management/v1/catalogs/lake/catalog-roles/catalog_admin/grants" \
  -d '{"type": "catalog", "privilege": "CATALOG_MANAGE_CONTENT"}'
echo "grants applied"
