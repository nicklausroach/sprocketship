
var userResult = snowflake.execute({sqlText: `SELECT CURRENT_USER()`});
userResult.next();

var currentUser = userResult.getColumnValue(`CURRENT_USER()`);
var databaseName = DATABASE_NAME;

var sqlCommands = [
    `CREATE DATABASE ${databaseName}`,
    `CALL SANDBOX.NICKROACH.CREATE_DATABASE_WRITER('${databaseName}');`,
    `CALL SANDBOX.NICKROACH.CREATE_DATABASE_READER('${databaseName}');`,
    `GRANT ROLE ${databaseName}_READER, ${databaseName}_WRITER TO USER ${currentUser};`,
    `GRANT ROLE ${databaseName}_READER, ${databaseName}_WRITER TO ROLE ACCOUNTADMIN;`
]

var resultSet = sqlCommands.map(command => snowflake.execute({sqlText: command}));

return`Database ${databaseName.toUpperCase()} created successfully.`;