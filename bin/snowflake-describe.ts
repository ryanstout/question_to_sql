#!/usr/bin/env node
// https://github.com/remix-run/remix/blob/main/packages/remix-dev/env.ts
import { Command } from "commander"
import type { LogLevelNames } from "loglevel"
import log from "loglevel"
import logLevelPrefix from "loglevel-plugin-prefix"
import { Snowflake } from "snowflake-multisql"
import invariant from "tiny-invariant"

import { loadEnv } from "@remix-run/dev/dist/env"

function configureLogging() {
  // TODO extract out to separate logging config
  // add expected log level prefixes
  logLevelPrefix.reg(log)
  log.enableAll()
  logLevelPrefix.apply(log)

  if (process.env.LOG_LEVEL) {
    const logLevelFromEnv = process.env.LOG_LEVEL.toLowerCase() as LogLevelNames
    log.setLevel(logLevelFromEnv)
  } else {
    log.setLevel(log.levels.INFO)
  }
}

// I checked underscore, rambda, and lodash and none has something simple like `fetch` in ruby :/
function fetch(ob: any, key: string) {
  if (key in ob) {
    return ob[key]
  }

  throw new Error(`Key does not exist: ${key}`)
}

// TODO wrap this up into a nice little config function
// TODO replace console.dir with custom method with better formatting
const util = require("util")
declare global {
  var dir: InstanceType<typeof Function>
  var toJson: InstanceType<typeof Function>
  var copyToClipboard: InstanceType<typeof Function>
}
// https://nodejs.org/api/util.html
util.inspect.defaultOptions.maxArrayLength = null
util.inspect.defaultOptions.colors = true
// TODO check if globals are accessible in a repl
global.dir = (ob: any) => process.stdout.write(util.inspect(ob))

function toJson(obj: any) {
  const jsonStr = JSON.stringify(obj, undefined, 2)
  copyToClipboard(jsonStr)
  console.log(jsonStr)
  return jsonStr
}
global.toJson = toJson

// copyToClipboard = (text) => {
function copyToClipboard(text: string) {
  require("child_process").spawnSync("/usr/bin/pbcopy", [], {
    env: {
      LC_CTYPE: "UTF-8",
    },
    input: text,
  })
}
global.copyToClipboard = copyToClipboard

// https://github.com/nodejs/node/issues/9617
function isDebugEnabled() {
  // even when using `node inspect` internally it gets transformed into --inspect-brk, which is why we check for this
  const inspectPassedOverCLI =
    process.execArgv.filter(
      (a) => a.includes("--inspect-brk") || a == "inspect"
    ).length > 0
  return require("inspector").url() !== undefined || inspectPassedOverCLI
}

function repl(context: any) {
  if (isDebugEnabled()) {
    // TODO `error` does not display any colored text... really?
    console.error("ERROR: Debug mode enabled, do not use repl!")
    return
  }

  console.log("Starting REPL...")

  const repl = require("repl")
  const replServer = repl.start({
    prompt: "snowflake> ",
    input: process.stdin,
    output: process.stdout,
    useGlobal: true,
  })

  // TODO remove all 'const ' from the input to avoid redeclaring variables error

  // list out all local variables
  replServer.defineCommand("vars", {
    help: "List all local variables",
    action: function () {
      this.displayPrompt()
      console.log(Object.keys(this.context))
    },
  })

  for (const key in context) {
    replServer.context[key] = context[key]
  }
}

// TODO I never was able to get this working...
// TODO `with` hack https://stackoverflow.com/questions/2051678/getting-all-variables-in-scope
function tsRepl(context: any) {
  // https://typestrong.org/ts-node/api/index.html#createRepl
  const tsNode = require("ts-node")
  const repl = tsNode.createRepl()
  const service = tsNode.create({ ...repl.evalAwarePartialHost })
  repl.setService(service)
  repl.start()

  // for(const key in context) {
  //   repl.context[key] = context[key];
  // }
}

// TODO `snowflake> Uncaught Error [ClientError]: Connection already terminated. Cannot connect again.`
export async function snowflakeConnection() {
  const snowflake = new Snowflake({
    account: fetch(process.env, "SNOWFLAKE_ACCOUNT"),
    username: fetch(process.env, "SNOWFLAKE_USER"),
    password: fetch(process.env, "SNOWFLAKE_PASSWORD"),

    // Warehouse > Database > Schema > Tables is the grouping hierarchy in snowflake
    // database: fetch(process.env, 'SNOWFLAKE_DATABASE'),
    // schema: fetch(process.env, 'SNOWFLAKE_DATABASE'),
    // TODO unsure why warehouse is even an option, maybe if you have more than one warehouse in your snowflake account?
    // warehouse: "DEMO_WH",
  })

  await snowflake.connect()

  return snowflake
}

// TODO incomplete, dump all schema on an account to determine which one we should filter on
async function listSchemas(snowflake: Snowflake) {
  const sqlText = "show schemas;"
  // tags are SQL variable bindings (terrible name)
  const schemaInAccount = await snowflake.executeAll({
    sqlText,
    tags: [],
    includeResults: true,
    preview: false, // set it true for checking statements before sending to Snowflake.
  })

  // the entire schema list is returned in a single row
  console.dir(schemaInAccount[0].data)

  repl({ snowflake })
}

export async function executeSQL<T>(snowflake: Snowflake, sql: string) {
  const result = await snowflake.executeAll<T>({
    sqlText: sql,
    tags: [],
    includeResults: true,
    preview: false,
  })

  // TODO no idea why the return value is a list, and the type seems to indicate it's an object
  if (result.length > 1) {
    throw new Error("Expected only one return data")
  }

  // strip out undefined from the return types
  const resultData = result[0].data
  invariant(resultData !== undefined)
  return resultData
}

async function describeTableAsSQL(
  snowflake: Snowflake,
  fullyQualifiedTableName: string
): Promise<string> {
  const result = await executeSQL<{ [key: string]: string }>(
    snowflake,
    `SELECT GET_DDL('TABLE', '${fullyQualifiedTableName}');`
  )

  /*
  the resulting data structure is:
  [
    {
      "GET_DDL('TABLE', 'DAYSPRINGPENS.SHOPIFY_SCHEMA.ABANDONED_CHECKOUTS')": "FULL_SQL"
    }
  ]
  */

  if (result.length > 1) {
    throw new Error("Expected only one row")
  }

  const values = Object.values(result[0])

  if (values.length > 1) {
    throw new Error("Expected only one value")
  }

  return values[0]
}

// SELECT columnName FROM TABLE_NAME WHERE XYZ
interface ColumnMetadata {
  // is there any data in column? If every value is null, or default value
  //
}

// no indexes on a columar datastore
interface DataSourceColumnDefinition {
  name: string
  type: string
  kind: string
  "null?": string
  default: any
  "primary key": string
  "unique key": string
  check: any
  expression: any
  comment: any
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
  )
  // TODO filter out desribes that are not columns
  debugger
  return result
}

export interface TableDescription {
  created_on: string
  name: string
  database_name: string
  schema_name: string
  kind: string
  comment: string
  cluster_by: string
  rows: number
  bytes: number
  owner: string
  retention_time: string
  automatic_clustering: string
  change_tracking: string
  is_external: string
}

async function shouldIncludeTable(
  database: Snowflake,
  fullyQualifiedTableName: string
): Promise<boolean> {
  const SKIP_PREFIXES = [
    "_AIRBYTE",
    "DRAFT_ORDERS",
    "ABANDONED_CHECKOUTS",
    "FULFILLMENTS",
  ]
  const SKIP_SUFFIXES = ["_SCD"]

  const tableName = fullyQualifiedTableName.split(".").at(-1)
  invariant(tableName !== undefined)

  if (SKIP_PREFIXES.some((prefix) => tableName.startsWith(prefix))) {
    log.debug("excluding table", { table: fullyQualifiedTableName })
    return false
  }

  if (SKIP_SUFFIXES.some((suffix) => tableName.endsWith(suffix))) {
    log.debug("excluding table", { table: fullyQualifiedTableName })
    return false
  }

  // const countResult = await executeSQL<{ ["COUNT"]: number }>(
  //   database,
  //   `SELECT COUNT(*) as count FROM ${fullyQualifiedTableName}`
  // )

  // if (countResult[0].COUNT === 0) {
  //   log.debug("excluding empty table", {
  //     table: fullyQualifiedTableName,
  //   })
  //   return false
  // }

  return true
}

async function describeTables(snowflake: Snowflake, database: string) {
  const showTablesSql = "SHOW TABLES IN DATABASE " + database
  const snowflakeTableList = await executeSQL<TableDescription>(
    snowflake,
    showTablesSql
  )

  log.debug("all tables", { count: snowflakeTableList.length })

  let tableDescribeMap: { [key: string]: string } = {}

  for (const tableMeta of snowflakeTableList) {
    const fullyQualifiedTableName = `${tableMeta.database_name}.${tableMeta.schema_name}.${tableMeta.name}`

    if (
      (await shouldIncludeTable(snowflake, fullyQualifiedTableName)) === false
    ) {
      continue
    }

    log.debug(`describing table ${fullyQualifiedTableName}`)

    // alternatively, use `await describeTable(snowflake, database)` to return table as a JSON array
    tableDescribeMap[tableMeta.name] = cleanSnowflakeSQLDescribe(
      await describeTableAsSQL(snowflake, fullyQualifiedTableName)
    )
  }

  return tableDescribeMap
}

function cleanSnowflakeSQLDescribe(sqlDescribe: string) {
  return (
    sqlDescribe
      // uppercase takes more tokens, lowercase everything
      .toLowerCase()
      // "create or replace" => "create"
      .replace("create or replace", "create")
      // VARCHAR(\d) => TEXT
      .replace(/varchar\([\d,]+\)/g, "text")
      // number(38,0) => number
      .replace(/number\([\d,]+\)/g, "number")
      // timestamp_tz(9) => timestamp
      .replace(/timestamp_tz\([\d,]+\)/g, "timestamp")
      // cluster by (_AIRBYTE_EMITTED_AT) => ""
      .replace(/cluster by \([^)]+\)/g, "")
      // \n\t_AIRBYTE_UNIQUE_KEY VARCHAR(32), => "" (remember, everything is lowercase at this point)
      .replace(/\t\_airbyte\_.*/g, "")
      // remove duplicate lines
      .replace(/\n{2,}/gm, "\n")
      // remove all tabs
      .replace(/\t/g, "")
      // remove trailing semicolon
      .replace(/;$/gm, "")
  )
}

async function init() {
  process.chdir(__dirname + "/..")
  await loadEnv("")
  configureLogging()
}

async function main({
  databaseName,
  outputFile,
}: {
  databaseName: string
  outputFile: string
}) {
  await init()

  log.info("collecting all tables for SQL dump")
  const connection = await snowflakeConnection()
  const tableMap = await describeTables(connection, databaseName)

  const jsonMap = JSON.stringify(tableMap, undefined, 2)

  log.info(`writing table map to ${outputFile}.json`)
  Object.values(jsonMap).join("\n")

  require("fs").writeFileSync(`${outputFile}.json`, jsonMap)
  require("fs").writeFileSync(
    `${outputFile}.sql`,
    Object.values(tableMap).join("\n")
  )

  // TODO dump into DB tables

  repl({ tableMap })
}

async function snowflakeRepl() {
  await init()

  const connection = await snowflakeConnection()
  repl({
    connection,
    executeSQL: (sql: string) => executeSQL(connection, sql),
  })
}

const program = new Command()
program.option("--cli", "open up a snowflake repl", false)
program.option(
  "--database <database>",
  "snowflake database to dump",
  "DAYSPRINGPENS"
)
program.option("--output <output>", "output file prefix", "snowflake")
program.parse(process.argv)
const options = program.opts()

if (options.cli) {
  snowflakeRepl()
} else {
  main({ databaseName: options.database, outputFile: options.output })
}
