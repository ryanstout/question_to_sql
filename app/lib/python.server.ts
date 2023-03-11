// NOTE this file is tightly coupled to the question.server, but extracted out so we can easily mock it in tests
import invariant from "tiny-invariant"

import axios, { AxiosError } from "axios"

import { isMockedPythonServer } from "~/lib/environment"
import { log } from "~/lib/logging"

import * as Sentry from "@sentry/remix"

export function throwIfNotPythonError(error: any) {
  if (error instanceof SyntaxError || error instanceof AxiosError) {
    Sentry.captureException(error)
    return
  }

  throw error
}

// runs SQL and gets a result, lower-level function which should not be run directly
export async function runQuery(
  dataSourceId: number,
  sql: string,
  allow_cached_queries: boolean
) {
  if (isMockedPythonServer()) {
    return Promise.resolve([{ count: 100 }])
  }

  const response = await pythonRequest("/query", {
    data_source_id: dataSourceId,
    sql: sql,
    allow_cached_queries: allow_cached_queries,
  })

  return response["results"]
}

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
  const response = await axios(postURL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    data: requestParams,

    // fly.io has a 60s proxy timeout
    timeout: 59_000,
  })

  const json = await response.data
  return json
}
