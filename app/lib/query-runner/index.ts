import { runQuery as runQueryPostgres } from "./postgres"
import { runQuery as runQuerySnowflake } from "./snowflake"

export async function runQuery(
  dataSource: any,
  querySQL: string
): Promise<any[]> {
  // TODO remove me! Use mock server once we have a python API
  if (process.env.MOCKED_QUESTION_RESPONSE === "true") {
    return new Promise((resolve, reject) => {
      resolve([{ count: 100 }])
    })
  }

  if (dataSource.type == "snowflake") {
    return runQuerySnowflake(dataSource, querySQL)
  } else if (dataSource.type == "postgres") {
    return runQueryPostgres(dataSource, querySQL)
  } else {
    throw new Error("Unsupported data source type: " + dataSource.type)
  }
}

export default {
  runQuery,
}
