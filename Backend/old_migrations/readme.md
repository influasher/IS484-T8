# Liquibase PostgreSQL

This project uses Liquibase to manage database schema migrations for a PostgreSQL database. The migration scripts define and apply schema changes in a version-controlled, repeatable manner.


## Project Structure

```
/migrations
│
├── /db
│   ├── /changelog
│   │   ├── db.changelog-master.xml          # Main changelog file
│   │   ├── changeset-initial-stage-1.xml                  # Modular changeset file
│   │   └── ...                             # Additional changelog files
│   └── /migration-scripts                  # Raw SQL scripts for complex migrations
│       ├── 001_initial_schema.sql
│       ├── ...
│
├── liquibase.properties                     # Configuration file for Liquibase
└── README.md                                # Project documentation
```


## Prerequisites
### Install Required Tools
1. Liquibase: Download and install Liquibase.
2. PostgreSQL: Ensure PostgreSQL is installed and running.

### Setup

1. Configure the database connection in the liquibase.properties 
2. Replace the placeholders with your database details.
3. Verify the setup:

```
liquibase status
```

## Applying Changes
To apply the changes defined in the changelog files:

```
liquibase update
```

This will:
- Execute the SQL scripts or changes defined in the changelog.
- Update the database schema.
- Track applied changes in the DATABASECHANGELOG table.


## Managing Changes
### Preview SQL Changes
To preview the SQL that Liquibase will execute:

```
liquibase updateSQL
```

### Rollback Changes
To roll back the last changeset:
```
liquibase rollbackCount 1
```

### Generate ChangeLog from Existing Database
To create a changelog from an existing schema:
```
liquibase generateChangeLog
```

## Troubleshooting
### Common Issues

1. Database Connection Errors:
    - Verify that the url, username, and password in liquibase.properties are correct.
    - Ensure the PostgreSQL server is running and accessible.
2. Lock Issues:
    - If the DATABASECHANGELOGLOCK table is locked, release it:

```
UPDATE DATABASECHANGELOGLOCK SET LOCKED = FALSE WHERE ID = 1;
```

## File Description
- `liquibase.properties`: Configures database connection and changelog file path.

- `db.changelog-master.xml`: The master changelog file that references all other changelog files.

- `/db/migration-scripts`: Contains raw SQL files for complex or vendor-specific changes.

