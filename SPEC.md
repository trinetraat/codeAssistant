# Org coding standards

- All timestamps in UTC, ISO 8601 format.
- Use snake_case for table/column names, ≤30 chars.
- Azure Functions: Python 3.11, include function.json, requirements.txt.
- Fabric pipelines: write parquet with pyarrow, safe types for Synapse.
- CI/CD: build → test → deploy stages in YAML.