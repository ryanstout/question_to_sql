import { renderToString } from "react-dom/server"

import type { EntryContext } from "@remix-run/node"
import { RemixServer } from "@remix-run/react"

import { createStylesServer, injectStyles } from "@mantine/remix"

// import in order to configure the global logger
import logger from "~/lib/logging.server"

const server = createStylesServer()

export default function handleRequest(
  request: Request,
  responseStatusCode: number,
  responseHeaders: Headers,
  remixContext: EntryContext
) {
  let markup = renderToString(
    <RemixServer context={remixContext} url={request.url} />
  )
  responseHeaders.set("Content-Type", "text/html")

  return new Response(`<!DOCTYPE html>${injectStyles(markup, server)}`, {
    status: responseStatusCode,
    headers: responseHeaders,
  })
}
