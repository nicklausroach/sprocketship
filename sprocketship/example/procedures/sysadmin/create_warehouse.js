// Configuration for this procedure is defined in .sprocketship.yml
// This demonstrates the YAML configuration pattern with arguments that have default values

var warehouseName = WAREHOUSE_NAME;
var warehouseSize = WAREHOUSE_SIZE;        // Defaults to 'XSMALL' if not provided
var autoSuspend = AUTO_SUSPEND;            // Defaults to 300 if not provided

var sqlCommands = [
    `CREATE OR REPLACE WAREHOUSE ${warehouseName}
     WITH WAREHOUSE_SIZE = ${warehouseSize}
     AUTO_SUSPEND = ${autoSuspend}
     AUTO_RESUME = TRUE
     INITIALLY_SUSPENDED = TRUE`
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

return `Warehouse ${warehouseName} created successfully with size ${warehouseSize} and auto-suspend ${autoSuspend} seconds.`;
