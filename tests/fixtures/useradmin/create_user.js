var username = USERNAME;
var password = PASSWORD;
var query = `CREATE USER ${username} PASSWORD = '${password}'`;
snowflake.execute({sqlText: query});
return `User ${username} created successfully`;
