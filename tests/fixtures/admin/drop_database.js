/*
comment: Drops a database - overriding config in frontmatter
*/
var databaseName = DATABASE_NAME;
var query = `DROP DATABASE ${databaseName}`;
snowflake.execute({sqlText: query});
return `Database ${databaseName} dropped successfully`;
