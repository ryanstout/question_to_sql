import {
  Cardinality,
  ColumnValues,
  Columns,
  Count,
  Query,
  TableNames,
} from "~/models/query.server"

export async function GenerateSchema(limit: number = 30, withComments = false) {
  const tableNames = await TableNames()
  const comment = withComments ? "-- " : ""
  const originalLimit = limit

  for await (const tableName of tableNames) {
    console.log(`${comment}CREATE TABLE ${tableName} (`)
    // Loop through each field
    const columns = await Columns(tableName)
    var i = 0
    for await (const column of columns) {
      // console.log(column)
      // console.log('  - ', column.column_name, column.data_type)

      const columnName = column.column_name
      const dataType = column.data_type

      const skip =
        tableName === "software_updates" ||
        columnName === "pledge_level" ||
        (columnName === "software_package_url" &&
          tableName === "orders" &&
          columnName === "status") || // weird field we don't use anymore
        (tableName === "orders" && columnName === "source") // more unused

      if (!skip) {
        const defaultValue = column.column_default
        let defaultStr = ""
        if (defaultValue && !defaultValue.match(/nextval/)) {
          defaultStr = ` DEFAULT ${defaultValue}`
        }

        const nullable = column.is_nullable
        let nullableStr
        if (nullable && nullable == "YES") {
          nullableStr = ""
        } else {
          nullableStr = " NOT NULL"
        }

        let comma = ","
        if (i == columns.length - 1) {
          comma = ""
        }

        let cardComment = ""

        const forceIncludes = [
          "shipping_state",
          "shipping_country",
          "shipping_name",
        ].includes(columnName)

        if (
          (dataType === "character varying" &&
            columnName.indexOf('"') === -1) ||
          forceIncludes
        ) {
          try {
            if (columnName === "shipping_country") {
              limit = 1000
            } else {
              limit = originalLimit
            }

            const cardinality = await Cardinality(tableName, columnName)
            const cardinalityInt = parseInt(cardinality[0].count) as number

            const count = await Count(tableName)
            const countInt = parseInt(count[0].count) as number

            const percentOfUnique = cardinalityInt / countInt
            // console.log('card: ', cardinalityInt, ' count: ', countInt, ' percent: ', percentOfUnique)

            // if (percentOfUnique < 0.05) {
            if (cardinalityInt < 150 || forceIncludes) {
              const columnValues = await ColumnValues(
                tableName,
                columnName,
                limit
              )
              const columnValuesCSV = columnValues.map((columnValue) => {
                return JSON.stringify(columnValue[columnName])
              })

              if (cardinalityInt > limit) {
                cardComment = ` -- values include but are not limited to: ${columnValuesCSV
                  .slice(0, limit)
                  .join(", ")}...`
              } else {
                cardComment = ` -- choices: ${columnValuesCSV.join(", ")}`
              }
            }
          } catch (e) {
            console.log("err: ", e)
          }
        }
        const commentSpaces = withComments ? "   " : "    "
        console.log(
          `${comment}${commentSpaces}${columnName} ${dataType}${defaultStr}${nullableStr}${comma}${cardComment}`
        )
      }

      i += 1
    }

    console.log(`${comment});`)
  }

  console.log("\n\n")
}

GenerateSchema(30, false)
