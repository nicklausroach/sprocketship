var databaseName = DATABASE_NAME;
var roleName = `${databaseName}_WRITER`;

var sqlCommands = [
    `CREATE OR REPLACE ROLE ${roleName}`,
    `GRANT OWNERSHIP ON DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT OWNERSHIP ON ALL TABLES IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT OWNERSHIP ON FUTURE TABLES IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT OWNERSHIP ON ALL VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT OWNERSHIP ON FUTURE VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT OWNERSHIP ON FUTURE SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT CREATE SCHEMA ON DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT CREATE TABLE, CREATE VIEW, CREATE STAGE, CREATE FILE FORMAT, CREATE SEQUENCE, CREATE FUNCTION, CREATE PROCEDURE, CREATE TASK, CREATE PIPE ON ALL SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT CREATE TABLE, CREATE VIEW, CREATE STAGE, CREATE FILE FORMAT, CREATE SEQUENCE, CREATE FUNCTION, CREATE PROCEDURE, CREATE TASK, CREATE PIPE ON FUTURE SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON ALL TABLES IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON FUTURE TABLES IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON ALL VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON FUTURE VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
]

for (i in sqlCommands) {
    try {
        snowflake.execute( {sqlText: sqlCommands[i]} );
    }
    catch (err)  {
        result = "Command: " + sqlCommands[i];
        result += "\nExecuted as Role: " + currentRole;
        result +=  "\nFailed: Code: " + err.code + "\n  State: " + err.state;
        result += "\n  Message: " + err.message;
        result += "\nStack Trace:\n" + err.stackTraceTxt; 
        return result;
    }
}

return "Writer created successfully.";
