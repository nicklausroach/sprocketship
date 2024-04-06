var databaseName = DATABASE_NAME;
var roleName = `${databaseName}_WRITER`;

var sqlCommands = [
    `CREATE OR REPLACE ROLE ${roleName}`
    `GRANT OWNERSHIP ON DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT OWNERSHIP ON ALL TABLES IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT OWNERSHIP ON ALL VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT OWNERSHIP ON ALL FUTURE VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT CREATE SCHEMA ON DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT OWNERSHIP, CREATE TABLE, CREATE VIEW, CREATE STAGE, CREATE FILE FORMAT, CREATE SEQUENCE, CREATE FUNCTION, CREATE PIPE ON ALL SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT OWNERSHIP, CREATE TABLE, CREATE VIEW, CREATE STAGE, CREATE FILE FORMAT, CREATE SEQUENCE, CREATE FUNCTION, CREATE PIPE ON FUTURE SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON ALL TABLES IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON FUTURE TABLES IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON ALL VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON FUTURE VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
]

var resultSet = sqlCommands.map(command => snowflake.execute({sqlText: command}));

return "Writer created successfully.";
