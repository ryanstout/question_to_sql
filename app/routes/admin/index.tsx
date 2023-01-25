import { useState } from "react"
import { z } from "zod"
import { zx } from "zodix"

import { ActionArgs, LoaderFunction, redirect } from "@remix-run/node"
import { Form } from "@remix-run/react"

import { Center, TextInput, Title } from "@mantine/core"

import { prisma } from "~/db.server"
import { HeaderMenu } from "~/components/dashboard/headerMenu"
import { Hero } from "~/routes/hero"
import { findOrCreateQuestionGroup } from "~/routes/admin/$questionGroupId"
import { requireUserId } from "~/session.server"
import { useOptionalUser } from "~/utils"

export async function action({ request }: ActionArgs) {
  const userId = await requireUserId(request)

  // TODO in what case would input query be optional?
  const { q } = await zx.parseForm(request, {
    q: z.string().optional(),
  })

  const questionGroup = await findOrCreateQuestionGroup(userId, null)

  if (q) {
    return redirect(
      `/query/${questionGroup.id}/chart/raw?q=${encodeURIComponent(
        q as string
      )}`
    )
  } else {
    return redirect(`/query/${questionGroup.id}/chart/raw`)
  }
}

export default function Index() {
  // TODO we need to require user login at this stage
  const user = useOptionalUser()
  const [question, setQuestion] = useState("")

  return (
    <>
      <main>
        <Center sx={{ height: "100vh" }}>
          {/* TODO I don't think we need an explicit action here? */}
          <Form action="/query" method="post">
            <Title>What would you like to know?</Title>
            <TextInput
              name="q"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </Form>
        </Center>
      </main>
    </>
  )
}