import { Center, TextInput, Title } from "@mantine/core"
import type { ActionArgs } from "@remix-run/node"
import { LoaderFunction, redirect } from "@remix-run/node"
import { Form } from "@remix-run/react"
import { useState } from "react"
import { z } from "zod"
import { zx } from "zodix"
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
      `/admin/${questionGroup.id}/chart/raw?q=${encodeURIComponent(
        q as string
      )}`
    )
  } else {
    return redirect(`/admin/${questionGroup.id}/chart/raw`)
  }
}

export const loader: LoaderFunction = async ({ request }) => {
  await requireUserId(request)
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
          <Form action="/admin" method="post">
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
