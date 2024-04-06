var databaseName = DATABASE_NAME;
var roleName = `${databaseName}_READER`;

var sqlCommands = [
    `CREATE OR REPLACE ROLE ${roleName}`
    `GRANT USAGE ON DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT USAGE ON ALL SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT USAGE ON ALL FUTURE SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName}  REVOKE CURRENT GRANTS;`,
    `GRANT SELECT ON ALL TABLES IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT SELECT ON FUTURE TABLES IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT SELECT ON ALL VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT SELECT ON FUTURE VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
]

var resultSet = sqlCommands.map(command => snowflake.execute({sqlText: command}));

return "Reader created successfully.";