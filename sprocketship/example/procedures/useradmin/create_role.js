/*
args:
  - name: role_name
    type: varchar
returns: varchar
comment: |
  Creates a role with the provided name
*/
var roleName = ROLE_NAME;

var sqlCommands = [
    `CREATE OR REPLACE ROLE ${roleName}`
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
