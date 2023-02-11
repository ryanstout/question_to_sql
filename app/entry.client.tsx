import { useEffect } from "react"
import { hydrate } from "react-dom"

import { RemixBrowser, useLocation, useMatches } from "@remix-run/react"

import { ClientProvider } from "@mantine/remix"

import * as Sentry from "@sentry/remix"

hydrate(
  <ClientProvider>
    <RemixBrowser />
  </ClientProvider>,
  document
)

// TODO should use helper for this
if (process.env.NODE_ENV === "production") {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    tracesSampleRate: 1,
    integrations: [
      new Sentry.BrowserTracing({
        routingInstrumentation: Sentry.remixRouterInstrumentation(
          useEffect,
          useLocation,
          useMatches
        ),
      }),
    ],
  })
}
