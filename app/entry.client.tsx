import * as Sentry from "@sentry/remix"
import { startTransition, useEffect } from "react"
import { hydrateRoot } from "react-dom/client"

import { RemixBrowser, useLocation, useMatches } from "@remix-run/react"

import { ClientProvider } from "@mantine/remix"

const hydrate = () => {
  startTransition(() => {
    hydrateRoot(
      document,
      // <StrictMode>
      <ClientProvider>
        <RemixBrowser />
      </ClientProvider>
      // </StrictMode>
    )
  })
}

if (window.requestIdleCallback) {
  window.requestIdleCallback(hydrate)
} else {
  // Safari doesn't support requestIdleCallback
  // https://caniuse.com/requestidlecallback
  window.setTimeout(hydrate, 1)
}

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
    // ...
  })
}
