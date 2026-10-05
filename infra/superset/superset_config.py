# Local demo configuration. Values here are throwaway, not secrets.
SECRET_KEY = "local-demo-only-change-me"
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"
FEATURE_FLAGS = {"DASHBOARD_RBAC": False}
# The sync script talks to the REST API with a session cookie and a CSRF token.
WTF_CSRF_ENABLED = True
