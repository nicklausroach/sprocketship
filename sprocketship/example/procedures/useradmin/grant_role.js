// Configuration for this procedure is defined in .sprocketship.yml
// This demonstrates a procedure with multiple required arguments (no defaults)

var roleName = ROLE_NAME;
var userName = USER_NAME;

var sqlCommands = [
    `GRANT ROLE ${roleName} TO USER ${userName}`
];

for (i in sqlCommands) {
    try {
        snowflake.execute({sqlText: sqlCommands[i]});
    }
    catch (err) {
        result = "Command: " + sqlCommands[i];
        result += "\nFailed: Code: " + err.code + "\n  State: " + err.state;
        result += "\n  Message: " + err.message;
        result += "\nStack Trace:\n" + err.stackTraceTxt;
        return result;
    }
}

return `Role ${roleName} granted to user ${userName} successfully.`;
