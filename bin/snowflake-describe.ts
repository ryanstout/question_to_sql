#!/usr/bin/env node
// https://github.com/remix-run/remix/blob/main/packages/remix-dev/env.ts
import { Snowflake, loadFiles } from "snowflake-multisql";
import invariant from "tiny-invariant";

import { loadEnv } from "@remix-run/dev/dist/env";

// I checked underscore, rambda, and lodash and none has something simple like `fetch` in ruby :/
function fetch(ob: any, key: string) {
  if (key in ob) {
    return ob[key];
  }

  throw new Error(`Key does not exist: ${key}`);
}

// TODO wrap this up into a nice little config function
// TODO replace console.dir with custom method with better formatting
const util = require("util");
declare global {
  var dir: InstanceType<typeof Function>;
}
// https://nodejs.org/api/util.html
util.inspect.defaultOptions.maxArrayLength = null;
util.inspect.defaultOptions.colors = true;
// TODO check if globals are accessible in a repl
global.dir = util.inspect;

function toJson(obj: any) {
  const jsonStr = JSON.stringify(obj, undefined, 2);
  copyToClipboard(jsonStr);
  console.log(jsonStr);
  return jsonStr;
}

// copyToClipboard = (text) => {
function copyToClipboard(text: string) {
  require("child_process").spawnSync("/usr/bin/pbcopy", [], {
    env: {
      LC_CTYPE: "UTF-8",
    },
    input: text,
  });
}

// https://github.com/nodejs/node/issues/9617
function isDebugEnabled() {
  // even when using `node inspect` internally it gets transformed into --inspect-brk, which is why we check for this
  const inspectPassedOverCLI =
    process.execArgv.filter(
      (a) => a.includes("--inspect-brk") || a == "inspect"
    ).length > 0;
  return require("inspector").url() !== undefined || inspectPassedOverCLI;
}

function repl(context: any) {
  if (isDebugEnabled()) {
    // TODO `error` does not display any colored text... really?
    console.error("ERROR: Debug mode enabled, do not use repl!");
    return;
  }

  console.log("Starting REPL...");

  const repl = require("repl");
  const replServer = repl.start({
    prompt: "snowflake> ",
    input: process.stdin,
    output: process.stdout,
    useGlobal: true,
  });

  // TODO remove all 'const ' from the input to avoid redeclaring variables error

  // list out all local variables
  replServer.defineCommand("vars", {
    help: "List all local variables",
    action: function () {
      this.displayPrompt();
      console.log(Object.keys(this.context));
    },
  });

  for (const key in context) {
    replServer.context[key] = context[key];
  }
}

// TODO I never was able to get this working...
// TODO `with` hack https://stackoverflow.com/questions/2051678/getting-all-variables-in-scope
function tsRepl(context: any) {
  // https://typestrong.org/ts-node/api/index.html#createRepl
  const tsNode = require("ts-node");
  const repl = tsNode.createRepl();
  const service = tsNode.create({ ...repl.evalAwarePartialHost });
  repl.setService(service);
  repl.start();

  // for(const key in context) {
  //   repl.context[key] = context[key];
  // }
}

// TODO `snowflake> Uncaught Error [ClientError]: Connection already terminated. Cannot connect again.`
export async function snowflakeConnection() {
  process.chdir(__dirname + "/..");
  await loadEnv("");

  const snowflake = new Snowflake({
    account: fetch(process.env, "SNOWFLAKE_ACCOUNT"),
    username: fetch(process.env, "SNOWFLAKE_USER"),
    password: fetch(process.env, "SNOWFLAKE_PASSWORD"),

    // Warehouse > Database > Schema > Tables is the grouping hierarchy in snowflake
    // database: fetch(process.env, 'SNOWFLAKE_DATABASE'),
    // schema: fetch(process.env, 'SNOWFLAKE_DATABASE'),
    // TODO unsure why warehouse is even an option, maybe if you have more than one warehouse in your snowflake account?
    // warehouse: "DEMO_WH",
  });

  await snowflake.connect();

  return snowflake;
}

// TODO incomplete, dump all schema on an account to determine which one we should filter on
async function listSchemas(snowflake: Snowflake) {
  const sqlText = "show schemas;";
  // tags are SQL variable bindings (terrible name)
  const schemaInAccount = await snowflake.executeAll({
    sqlText,
    tags: [],
    includeResults: true,
    preview: false, // set it true for checking statements before sending to Snowflake.
  });

  // the entire schema list is returned in a single row
  console.dir(schemaInAccount[0].data);

  repl({ snowflake });
}

// should be IExecuteAllResult
function extractSingleRowResult(result: any) {
  if (result.length > 1) {
    throw new Error("Expected only one row");
  }

  return result[0];
}

export async function executeSQL<T>(snowflake: Snowflake, sql: string) {
  const result = await snowflake.executeAll<T>({
    sqlText: sql,
    tags: [],
    includeResults: true,
    preview: false,
  });

  // TODO no idea why the return value is a list, and the type seems to indicate it's an object
  if (result.length > 1) {
    throw new Error("Expected only one return data");
  }

  // strip out undefined from the return types
  const resultData = result[0].data;
  invariant(resultData !== undefined);
  return resultData;
}

async function describeTableAsSQL(
  snowflake: Snowflake,
  fullyQualifiedTableName: string
): Promise<string> {
  const result = await executeSQL<{ [key: string]: string }>(
    snowflake,
    `SELECT GET_DDL('TABLE', '${fullyQualifiedTableName}');`
  );

  /*
  the resulting data structure is:
  [
    {
      "GET_DDL('TABLE', 'DAYSPRINGPENS.SHOPIFY_SCHEMA.ABANDONED_CHECKOUTS')": "FULL_SQL"
    }
  ]
  */

  if (result.length > 1) {
    throw new Error("Expected only one row");
  }

  const values = Object.values(result[0]);

  if (values.length > 1) {
    throw new Error("Expected only one value");
  }

  return values[0];
}

// SELECT columnName FROM TABLE_NAME WHERE XYZ
interface ColumnMetadata {
  // is there any data in column? If every value is null, or default value
  //
}

// no indexes on a columar datastore
interface DataSourceColumnDefinition {
  name: string;
  type: string;
  kind: string;
  "null?": string;
  default: any;
  "primary key": string;
  "unique key": string;
  check: any;
  expression: any;
  comment: any;
  // "policy name": any
}

// this SQL results in an array of json objects describing the fields
async function describeTable(
  snowflake: Snowflake,
  fullyQualifiedTableName: string
) {
  const result = await executeSQL<DataSourceColumnDefinition>(
    snowflake,
    `DESCRIBE TABLE ${fullyQualifiedTableName};`
  );
  // TODO filter out desribes that are not columns
  debugger;
  return result;
}

export interface TableDescription {
  created_on: string;
  name: string;
  database_name: string;
  schema_name: string;
  kind: string;
  comment: string;
  cluster_by: string;
  rows: number;
  bytes: number;
  owner: string;
  retention_time: string;
  automatic_clustering: string;
  change_tracking: string;
  is_external: string;
}

async function describeTables(snowflake: Snowflake, database: string) {
  const showTablesSql = "SHOW TABLES IN DATABASE " + database;
  const snowflakeTableList = await executeSQL<TableDescription>(
    snowflake,
    showTablesSql
  );

  const tableDescribeMap: { [key: string]: string } = {};

  for (const tableMeta of snowflakeTableList) {
    // exclude tables that start with "_AIRBYTE"
    if (tableMeta.name.startsWith("_AIRBYTE")) {
      continue;
    }

    const fullyQualifiedTableName = `${tableMeta.database_name}.${tableMeta.schema_name}.${tableMeta.name}`;
    console.log(`describing table ${fullyQualifiedTableName}`);

    // alternatively, use `await describeTable(snowflake, database)` to return table as a JSON array
    // tableDescribeMap[tableMeta.name] = await describeTableAsSQL(snowflake, fullyQualifiedTableName)
    tableDescribeMap[tableMeta.name] = await describeTable(
      snowflake,
      fullyQualifiedTableName
    );
  }

  return tableDescribeMap;
}

async function main() {
  const connection = await snowflakeConnection();
  const tableMap = await describeTables(connection, "DAYSPRINGPENS");

  // TODO dump into DB tables
}

async function snowflakeRepl() {
  const connection = await snowflakeConnection();
  repl({ connection, executeSQL });
}

main();

// TODO CLI option to open up a snowflake REPL
// snowflakeRepl()

function cleanSnowflakeSQLDescribe(describeMap) {
  // # column filters
  // uppercase takes more tokens, lowercase everything
  // "create or replace" => "create"
  // VARCHAR(\d) => TEXT
  // "cluster by (.*)" => remove airbyte stuff
  // SCD => slowly changing dimension tables, filter these
  // exclude airbyte columns
  // # table filters
  // exclude tables that do not have any data
  // exclude columns without any values
  // manually exclude some tables they aren't going to use
}

// var snowflakeTableJSON = require('fs').readFileSync('./snowflake.json')
// repl({ snowflakeTableJSON})
