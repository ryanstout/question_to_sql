import { useEffect } from "react"

import { RemixBrowser, useLocation, useMatches } from "@remix-run/react"

import { ClientProvider } from "@mantine/remix"

import * as Sentry from "@sentry/remix"
import { hydrateRoot } from "react-dom/client"

export function isProduction() {
  return process.env.NODE_ENV === "production"
}

// TODO may break emotion on the client side https://github.com/emotion-js/emotion/issues/2800
// TODO this is not correct, we should be using hydrateRoot, but it doesn't look like mantine supports this yet app/entry.client.tsx
hydrateRoot(
  document,
  <ClientProvider>
    <RemixBrowser />
  </ClientProvider>
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
