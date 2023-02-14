import { useEffect } from "react"
import { hydrate } from "react-dom"

import { RemixBrowser, useLocation, useMatches } from "@remix-run/react"

import { ClientProvider } from "@mantine/remix"

import * as Sentry from "@sentry/remix"
import { isProduction } from "./lib/environment.server"

// TODO may break emotion on the client side https://github.com/emotion-js/emotion/issues/2800
// TODO this is not correct, we should be using hydrateRoot, but it doesn't look like mantine supports this yet app/entry.client.tsx
hydrate(
  <ClientProvider>
    <RemixBrowser />
  </ClientProvider>,
  document
)

if (isProduction()) {
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
