// V1 of this using the pg package
import { Client } from "pg"
import postgres from "postgres"

export class UserDb {
  sql: postgres.Sql<{}>

  constructor() {
    // Connect to the user db
    this.sql = postgres({
      host: "localhost",
      database: "witharsenal_prod_copy",
    })
    console.log(this.sql)
  }

  async Query(query: string): Promise<Map<string, any>> {
    const result = await this.sql`${query}`

    const resultObjs = result.map((row) => {
      return Object.fromEntries(Object.entries(row))
    })
    return result
  }

  str(s: string) {
    return JSON.stringify(s)
  }

  async TableNames(): Promise<string[]> {
    const tables = await this
      .sql`SELECT table_name FROM information_schema.tables WHERE table_schema='public'`
    const tableNames = tables.map((table) => {
      return table["table_name"] as string
    })
    return tableNames
  }

  async Columns(tableName: string): Promise<postgres.RowList<postgres.Row[]>> {
    const columns = await this
      .sql`SELECT * FROM information_schema.columns WHERE table_name = ${tableName};`
    return columns
  }
  async ColumnValues(
    tableName: string,
    columnName: string,
    limit: number = 1000
  ): Promise<Map<string, string>> {
    const columns = await Query(
      `SELECT ${str(columnName)}, COUNT(*) as count FROM ${str(
        tableName
      )} GROUP BY ${str(columnName)} ORDER BY count DESC LIMIT ${limit};`,
      []
    )
    return columns
  }

  async Cardinality(
    tableName: string,
    columnName: string
  ): Promise<Map<string, string>> {
    const columns = await Query(
      `SELECT COUNT(DISTINCT(${str(columnName)})) as count FROM ${str(
        tableName
      )};`,
      []
    )
    return columns
  }

  async Count(tableName: string): Promise<Map<string, string>> {
    const columns = await Query(
      `SELECT COUNT(*) as count FROM ${str(tableName)};`,
      []
    )
    return columns
  }

  async close() {
    await this.sql.end()
  }
}
