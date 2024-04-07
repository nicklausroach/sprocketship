
var userResult = snowflake.execute({sqlText: `SELECT CURRENT_USER()`});
userResult.next();
var currentUser = userResult.getColumnValue(`CURRENT_USER()`);

var roleResult = snowflake.execute({sqlText: `SELECT CURRENT_ROLE()`});
roleResult.next();
var currentRole = roleResult.getColumnValue(`CURRENT_ROLE()`);

var databaseName = DATABASE_NAME.toUpperCase();
var ttl = parseInt(TTL);

const scheduledDropTimestamp = new Date();
scheduledDropTimestamp.setDate(scheduledDropTimestamp.getDate() + ttl);

var sqlCommands = [
    `CREATE DATABASE ${databaseName}`,
    `CALL SANDBOX.NICKROACH.CREATE_DATABASE_WRITER('${databaseName}');`,
    `CALL SANDBOX.NICKROACH.CREATE_DATABASE_READER('${databaseName}');`,
    `GRANT ROLE ${databaseName}_READER, ${databaseName}_WRITER TO USER ${currentUser};`,
    `GRANT ROLE ${databaseName}_READER, ${databaseName}_WRITER TO ROLE ACCOUNTADMIN;`,
    `INSERT INTO UTIL_DB.PROC_TABLES.TEMP_DATABASES (
        DATABASE_NAME,
        CREATED_BY,
        CREATED_AT,
        TTL,
        SCHEDULED_DROP_TIMESTAMP
    ) VALUES
        (
            '${databaseName}',
            '${currentUser}',
            '${new Date().toISOString()}',
            ${ttl},
            '${scheduledDropTimestamp.toISOString()}'
        )
    `,
    `
    CREATE OR REPLACE TASK ${databaseName}.PUBLIC.DROP_${databaseName}_TASK
    WAREHOUSE = PURINA
    SCHEDULE = '360 MINUTE'
    AS
    CALL SANDBOX.NICKROACH.DROP_DATABASE_IF_EXPIRED('${databaseName}', '${scheduledDropTimestamp}')
    `,
    `ALTER TASK ${databaseName}.PUBLIC.DROP_${databaseName}_TASK RESUME`
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

return`Database ${databaseName} created successfully.`;