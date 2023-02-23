import { useEffect } from "react"
import invariant from "tiny-invariant"

import { RemixBrowser, useLocation, useMatches } from "@remix-run/react"

import { ClientProvider } from "@mantine/remix"

import { isProduction } from "~/lib/environment"

import * as Sentry from "@sentry/remix"
import { hydrateRoot } from "react-dom/client"

// TODO may break emotion on the client side https://github.com/emotion-js/emotion/issues/2800
// TODO this is not correct, we should be using hydrateRoot, but it doesn't look like mantine supports this yet app/entry.client.tsx
hydrateRoot(
  document,
  <ClientProvider>
    <RemixBrowser />
  </ClientProvider>
)

if (isProduction()) {
  const { SENTRY_DSN } = process.env
  invariant(SENTRY_DSN, "SENTRY_DSN is not defined")

  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: 0.1,
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
