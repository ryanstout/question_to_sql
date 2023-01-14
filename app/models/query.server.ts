import { Client } from 'pg'
import postgres from 'postgres'

export async function Query(queryStr: string, args: string[] = []) {
    const client = new Client({
        host: 'localhost',
        database: 'witharsenal_prod_copy'
    })
    await client.connect()

    try {
        const res = await client.query(queryStr, args)

        return res.rows
    }
    catch (e) {
        console.log("QUERY ERROR: ", queryStr, "\n", e)
        throw e
    }
    finally {
        await client.end()
    }
}

function str(s: string) {
    return JSON.stringify(s)
}

export async function TableNames(): Promise<string[]> {
    const tables = await Query("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    const tableNames = tables.map((table) => { return table['table_name'] as string })
    return tableNames
}

export async function Columns(tableName: string): Promise<Map<string, any>> {
    const columns = await Query("SELECT * FROM information_schema.columns WHERE table_name = $1;", [tableName])
    return columns
}

export async function ColumnValues(tableName: string, columnName: string, limit: number = 1000): Promise<Map<string, any>> {
    const columns = await Query(`SELECT ${str(columnName)}, COUNT(*) as count FROM ${str(tableName)} GROUP BY ${str(columnName)} ORDER BY count DESC LIMIT ${limit};`, [])
    return columns
}


export async function Cardinality(tableName: string, columnName: string): Promise<Map<string, any>> {
    const columns = await Query(`SELECT COUNT(DISTINCT(${str(columnName)})) as count FROM ${str(tableName)};`, [])
    return columns
}


export async function Count(tableName: string): Promise<Map<string, any>> {
    const columns = await Query(`SELECT COUNT(*) as count FROM ${str(tableName)};`, [])
    return columns
}

