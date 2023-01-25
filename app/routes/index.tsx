import { AppShell } from "@mantine/core"
import type { ActionArgs } from "@remix-run/node"
import { json } from "@remix-run/node"
import { useActionData } from "@remix-run/react"
import { z } from "zod"
import { zx } from "zodix"
import AppFooter from "~/components/dashboard/footer"
import HeaderMenu from "~/components/dashboard/headerMenu"
import LandingSearch from "~/components/dashboard/landingSearch"
import { processQuestion } from "~/lib/question.server"
import { requireUserId } from "~/session.server"




// this is executed on the server side
export const action = async ({ request }: ActionArgs) => {
  const { q } = await zx.parseForm(request, {
    q: z.string(),
  })

  const userId = await requireUserId(request)
  const dataSourceId = 1
  const result = await processQuestion(userId, dataSourceId, q)

  return json({ q, sql })
}

export const loader: LoaderFunction = async ({ request }) => {
  const userId = await requireUserId(request)
  return userId;
}

export default function Index() {
  const loader = useActionData()

  return (
    <AppShell footer={<AppFooter />}>
      <HeaderMenu />
      <LandingSearch question={loader ? loader.q : ""} />
    </AppShell>
  )
}
function useRequiredUser() {
  throw new Error("Function not implemented.")
}
