import { Connection } from "postgresql-client"

function getConnection() {
  return new Connection({
    host: "localhost",
    database: "witharsenal_prod_copy",
  })
}

export async function runQuery(datasource: any, querySQL: string) {
  const db = getConnection()
  await db.connect()
  const result = await db.query(querySQL)
  await db.close()
  return result
}
