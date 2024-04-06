
var userResult = snowflake.execute({sqlText: `SELECT CURRENT_USER()`});
userResult.next();

var currentUser = userResult.getColumnValue(`CURRENT_USER()`);
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
    `
]

var resultSet = sqlCommands.map(command => snowflake.execute({sqlText: command}));

return`Database ${databaseName} created successfully.`;