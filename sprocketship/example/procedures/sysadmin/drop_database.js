// Configuration for this procedure is defined in .sprocketship.yml
// This demonstrates grant_usage pattern to control who can execute this procedure

var databaseName = DATABASE_NAME;

var sqlCommands = [
    `DROP DATABASE IF EXISTS ${databaseName}`
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

return `Database ${databaseName} dropped successfully.`;
