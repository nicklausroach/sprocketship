/*
args:
  - name: database_name
    type: varchar
returns: varchar
comment: |
  Creates a database with the provided name
*/
var databaseName = DATABASE_NAME;

var sqlCommands = [
    `CREATE OR REPLACE DATABASE ${databaseName}`
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
