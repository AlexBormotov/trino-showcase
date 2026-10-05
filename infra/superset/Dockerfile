FROM apache/superset:6.1.0
USER root
# The image ships without database drivers; Trino's SQLAlchemy dialect comes with the client.
RUN uv pip install --python /app/.venv/bin/python --no-cache "trino[sqlalchemy]==0.340.0"
USER superset
