var databaseName = DATABASE_NAME;
var query = `CREATE DATABASE ${databaseName}`;
snowflake.execute({sqlText: query});
return `Database ${databaseName} created successfully`;
