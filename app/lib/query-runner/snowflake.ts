import { Snowflake } from "snowflake-multisql"
import invariant from "tiny-invariant"

async function executeSQL<T>(snowflake: Snowflake, sql: string) {
  if (process.env.MOCKED_QUESTION_RESPONSE === "true") {
    return new Promise<T>((resolve, reject) => {
      resolve([{ count: 100 }])
    })
  }

  const result = await snowflake.executeAll<T>({
    sqlText: sql,
    tags: [],
    includeResults: true,
    preview: false,
  })

  // TODO no idea why the return value is a list, and the type seems to indicate it's an object
  if (result.length > 3) {
    throw new Error("Expected only one return data")
  }

  // strip out undefined from the return types
  const resultData = result[2].data
  invariant(resultData !== undefined, "Expected result data from snowflake")
  return resultData
}

async function snowflakeConnection(dataSource: any) {
  const credentials = dataSource.credentials
  const snowflake = new Snowflake({
    account: credentials.account,
    username: credentials.username,
    password: credentials.password,
    database: credentials.database,
    schema: credentials.schema,
    warehouse: credentials.warehouse,
  })

  // TODO probably want a connection pool for this over the long term?
  await snowflake.connect()

  return snowflake
}

export async function runQuery(
  dataSource: any,
  querySQL: string
): Promise<any[]> {
  const snowflake = await snowflakeConnection(dataSource)

  return executeSQL(
    snowflake,
    "use WAREHOUSE COMPUTE_WH; use FIVETRAN_DATABASE.SHOPIFY;\n" + querySQL
  )
}
