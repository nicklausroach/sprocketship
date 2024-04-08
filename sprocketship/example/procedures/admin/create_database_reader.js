var databaseName = DATABASE_NAME;
var roleName = `${databaseName}_READER`;

var sqlCommands = [
    `CREATE OR REPLACE ROLE ${roleName}`,
    `GRANT USAGE ON DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT USAGE ON ALL SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT USAGE ON FUTURE SCHEMAS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT SELECT ON ALL TABLES IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT SELECT ON FUTURE TABLES IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT SELECT ON ALL VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
    `GRANT SELECT ON FUTURE VIEWS IN DATABASE ${databaseName} TO ROLE ${roleName};`,
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

return "Reader created successfully.";