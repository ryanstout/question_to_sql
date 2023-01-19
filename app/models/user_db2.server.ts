// V2, haven't moved everything over yet
import { analyzeMetafile } from "esbuild"
import { Connection } from "postgresql-client"

type QueryRow = {
  [key: string]: any
}

interface QueryResult {
  fieldTypes: Map<string, string>
  results: QueryRow[]
}

export class UserDb {
  sql: Connection

  constructor() {
    // Connect to the user db
    this.sql = new Connection({
      host: "localhost",
      database: "witharsenal_prod_copy",
    })
  }
  async connect() {
    await this.sql.connect()
  }

  async query(query: string): Promise<QueryResult> {
    const queryResult = await this.sql.query(query, { fetchCount: 5000 })
    const fieldTypes = new Map(
      queryResult.fields!.map((field) => {
        return [field.fieldName, field.dataTypeName]
      })
    )
    const fields = queryResult.fields!

    // Convert to key => value's using field names
    let results = [] as QueryRow[]
    console.log("results!: ", queryResult.rows!.length)
    queryResult.rows!.forEach((rowData) => {
      let row = {} as {
        [key: string]: any
      }
      let i = 0
      fields.forEach((field) => {
        row[field.fieldName] = rowData[i]
        i += 1
      })

      results.push(row)
    })

    return {
      fieldTypes: fieldTypes,
      results: results,
    }
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
    await this.sql.close()
  }
}
