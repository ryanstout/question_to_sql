// NOTE this file is tightly coupled to the question.server, but extracted out so we can easily mock it in tests
import invariant from "tiny-invariant"

import { isMockedPythonServer } from "~/lib/environment"
import { log } from "~/lib/logging"

import Sentry from "@sentry/remix"

// runs SQL and gets a result, lower-level function which should not be run directly
export async function runQuery(
  dataSourceId: number,
  sql: string,
  allow_cached_queries: boolean
) {
  if (isMockedPythonServer()) {
    return new Promise((resolve, _reject) => {
      resolve([{ count: 100 }])
    })
  }

  const response = await pythonRequest("/query", {
    data_source_id: dataSourceId,
    sql: sql,
    allow_cached_queries: allow_cached_queries,
  })

  return response["results"]
}

class QueryRunError extends Error {}

// TODO we need an openapi spec for the python server so we have full stack typing
export async function pythonRequest(endpoint: string, requestParams: any) {
  const serverHost = process.env.PYTHON_SERVER
  invariant(serverHost, "PYTHON_SERVER env var not set")

  // endpoint intentionally contains the leading `/` for better grepping
  const postURL = `${serverHost}${endpoint}`

  log.debug("making python request", {
    requestParams,
    postURL,
  })

  // TODO if the request takes too long, this just times out and doesn't respond
  //      need to use axios or something to get a timeout, fetch doesn't have one :/
  const response = await fetch(postURL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestParams),
  })

  try {
    const json = await response.json()
    return json
  } catch (e: any) {
    // catch JSON parse errors and rethrow them with more context
    if (e instanceof SyntaxError) {
      Sentry.captureException(e)
      throw new QueryRunError("Could not run generated SQL against data source")
    } else {
      throw e
    }
  }
}
