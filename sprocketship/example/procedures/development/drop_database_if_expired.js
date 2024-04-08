var dropTimestamp = DROP_TIMESTAMP
var databaseName = DATABASE_NAME

var currentTimestamp = new Date();
var givenTimestamp = new Date(Date.parse(dropTimestamp));

if (currentTimestamp > givenTimestamp) {
try {
    snowflake.createStatement({sqlText: `DROP DATABASE IF EXISTS ${databaseName}`}).execute();
    return `Database dropped successfully`;
} catch (err) {
    return `Error dropping database: ` + err.message;
}
} else {
return `Database has not expired yet`;
}