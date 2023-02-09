import { getUser } from "./session.server"
import { theme } from "./theme"

import type { LoaderArgs, MetaFunction } from "@remix-run/node"
import { json } from "@remix-run/node"
import {
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "@remix-run/react"

import { MantineProvider, createEmotionCache } from "@mantine/core"
import { StylesPlaceholder } from "@mantine/remix"

export const meta: MetaFunction = () => ({
  charset: "utf-8",
  title: "Knolbe — Knowledge Search Tuned to Your Business",
  viewport: "width=device-width,initial-scale=1",
})

// We make the user available in root, then all children can useMatchesData to
// access it.
export async function loader({ request }: LoaderArgs) {
  return json({
    user: await getUser(request),
  })
}

createEmotionCache({ key: "mantine" })

export default function App() {
  return (
    <MantineProvider theme={theme} withGlobalStyles withNormalizeCSS>
      <html lang="en">
        <head>
          <StylesPlaceholder />
          <Meta />
          <Links />
        </head>
        <body>
          <Outlet />
          <ScrollRestoration />
          <Scripts />
          <LiveReload />
        </body>
      </html>
    </MantineProvider>
  )
}
