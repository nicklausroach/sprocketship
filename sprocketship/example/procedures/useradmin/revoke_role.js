// Configuration for this procedure is defined in .sprocketship.yml
// This demonstrates grant_usage with role restrictions

var roleName = ROLE_NAME;
var userName = USER_NAME;

var sqlCommands = [
    `REVOKE ROLE ${roleName} FROM USER ${userName}`
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

return `Role ${roleName} revoked from user ${userName} successfully.`;
