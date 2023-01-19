import { UserDb } from "~/models/user_db2.server"

export async function runQuery(datasource: any, querySQL: string) {
  const db = new UserDb()
  await db.connect()
  const result = await db.query(querySQL)
  await db.close()
  return result
}
