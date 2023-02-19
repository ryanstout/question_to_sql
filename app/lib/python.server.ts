// NOTE this file is tightly coupled to the question.server, but extracted out so we can easily mock it in tests
import invariant from "tiny-invariant"

import { isMockedPythonServer } from "~/lib/environment"
import { log } from "~/lib/logging"

// runs SQL and gets a result, lower-level function which should not be run directly
export async function runQuery(dataSourceId: number, sql: string) {
  if (isMockedPythonServer()) {
    return new Promise((resolve, reject) => {
      resolve([{ count: 100 }])
    })
  }

  const response = await pythonRequest("query", {
    data_source_id: dataSourceId,
    sql: sql,
  })

  return response["results"]
}

// TODO we need an openapi spec for the python server so we have full stack typing
export async function pythonRequest(endpoint: string, requestParams: any) {
  const serverHost = process.env.PYTHON_SERVER
  invariant(serverHost, "PYTHON_SERVER env var not set")

  const postURL = `${serverHost}/${endpoint}`

  log.debug("making python request", {
    requestParams,
    postURL,
  })

  const response = await fetch(postURL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestParams),
  })

  const json = await response.json()
  return json
}
