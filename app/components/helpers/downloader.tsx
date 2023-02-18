export default function processDownload(
  fileType: string,
  arrayOfJson: any[] | null | undefined,
  fileName: string = "download"
) {
  if (isInvalidDownload(fileType, arrayOfJson, fileName)) {
    return
  }

  switch (fileType) {
    case "json":
      performJSONDownload(arrayOfJson, fileName)
      break
    case "csv":
      performCSVDownload(arrayOfJson, fileName)
      break
  }
}

function isInvalidDownload(
  fileType: string,
  arrayOfJson: any[] | null | undefined,
  fileName: string
) {
  let isInvalid = false

  if (fileType == undefined) {
    isInvalid = true
  }

  if (
    arrayOfJson == undefined ||
    arrayOfJson == null ||
    arrayOfJson.length == 0
  ) {
    isInvalid = true
  }

  if (fileName == undefined) {
    isInvalid = true
  }

  return isInvalid
}

function performJSONDownload(
  arrayOfJson: any[] | null | undefined,
  fileName: string
) {
  performFileDownload(
    JSON.stringify(arrayOfJson, null, 2),
    "data:text/json;charset=utf-8,",
    fileName + ".json"
  )
}

function performCSVDownload(
  arrayOfJson: any[] | null | undefined,
  fileName: string
) {
  // TODO: this is not needed because the invalid download check is done in the caller but typescript is not smart enough to know that
  if (arrayOfJson == null || arrayOfJson == undefined) {
    return
  }

  const replacer = (key: string, value: any) => (value === null ? "" : value)
  const header = Object.keys(arrayOfJson[0])
  let csv = arrayOfJson.map((row) =>
    header
      .map((fieldName) => JSON.stringify(row[fieldName], replacer))
      .join(",")
  )
  csv.unshift(header.join(","))

  const csvString = csv.join("\r\n")

  performFileDownload(
    csvString,
    "data:text/csv;charset=utf-8,",
    fileName + ".csv"
  )
}

function performFileDownload(
  data: string,
  encodingType: string,
  fileName: string
) {
  const dataStr = encodingType + encodeURIComponent(data)
  let downloadAnchorNode = document.createElement("a")
  downloadAnchorNode.setAttribute("href", dataStr)
  downloadAnchorNode.setAttribute("download", fileName)
  document.body.appendChild(downloadAnchorNode)
  downloadAnchorNode.click()
  downloadAnchorNode.remove()
}
