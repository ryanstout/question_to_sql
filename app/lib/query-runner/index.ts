import { runQuery as runQueryPostgres } from "./postgres"
import { runQuery as runQuerySnowflake } from "./snowflake"

export async function runQuery(dataSource: any, querySQL: string) {
  if (dataSource.type == "snowflake") {
    return runQuerySnowflake(dataSource, querySQL)
  } else if (dataSource.type == "postgres") {
    return runQueryPostgres(dataSource, querySQL)
  }
}

export default {
  runQuery,
}
