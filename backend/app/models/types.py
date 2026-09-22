from sqlalchemy import JSON

# JSON works on SQLite and Postgres alike; swap for pgvector once Postgres lands.
JSONList = JSON
JSONDict = JSON
