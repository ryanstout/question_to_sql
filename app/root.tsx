import type { LoaderArgs, MetaFunction } from "@remix-run/node"
import { json } from "@remix-run/node"
import {
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  useLoaderData,
} from "@remix-run/react"

import { AppShell, MantineProvider, createEmotionCache } from "@mantine/core"
import { NotificationsProvider } from "@mantine/notifications"
import { StylesPlaceholder } from "@mantine/remix"

import KnolbeFooter from "./components/dashboard/footer"
import HeaderMenu from "./components/dashboard/headerMenu"
import { getUser } from "./session.server"
import { theme } from "./theme"

export const meta: MetaFunction = () => ({
  charset: "utf-8",
  title: "Knolbe — Knowledge Search Tuned to Your Business",
  viewport: "width=device-width,initial-scale=1",
})

export async function loader({ request }: LoaderArgs) {
  return json({
    // pass non-sensitive environment variables to the client
    ENV: {
      SENTRY_DSN: process.env.SENTRY_DSN,
      LOG_LEVEL: process.env.LOG_LEVEL,
    },
    // TODO this seems strange... is this used anywhere? Why wouldn't you just use `getUser`?
    // We make the user available in root, then all children can useMatchesData to
    // access it.
    user: await getUser(request),
  })
}

createEmotionCache({ key: "mantine" })

// TODO add error & catch boundaries here

export default function App() {
  const data = useLoaderData()

  return (
    <MantineProvider theme={theme} withGlobalStyles withNormalizeCSS>
      <NotificationsProvider position="top-right">
        <html lang="en">
          <head>
            <StylesPlaceholder />
            <Meta />
            <Links />
          </head>
          <body>
            <AppShell
              padding="md"
              header={<HeaderMenu />}
              footer={<KnolbeFooter />}
              styles={(theme) => ({
                main: {
                  backgroundColor:
                    theme.colorScheme === "dark"
                      ? theme.colors.dark[8]
                      : theme.colors.gray[0],
                },
              })}
            >
              <Outlet />
            </AppShell>
            <ScrollRestoration />
            <Scripts />
            <LiveReload />
            {/* this seems dangerous, but seems like the most obvious way to use process.env on the client */}
            <script
              dangerouslySetInnerHTML={{
                __html: `window.process = ${JSON.stringify({
                  env: data.ENV,
                })}`,
              }}
            />
          </body>
        </html>
      </NotificationsProvider>
    </MantineProvider>
  )
}
