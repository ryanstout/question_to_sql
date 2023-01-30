import type { Question } from "@prisma/client"
import { z } from "zod"
import { zx } from "zodix"

import type { ActionArgs } from "@remix-run/node"
import {
  Form,
  Link,
  useLoaderData,
  useNavigate,
  useParams,
} from "@remix-run/react"
import type { LoaderFunction } from "@remix-run/server-runtime"
// TODO: pagination logic should be abstracted
import { redirect } from "@remix-run/server-runtime"

import { Button, Container, Pagination, Table } from "@mantine/core"

import { prisma } from "~/db.server"
import { requireUserId } from "~/session.server"
import { toNum } from "~/utils"

type LoaderData = {
  result: Pick<Question, "id" | "question" | "questionGroupId">[]
  total: number
  limit: number
  offset: number
}

const defaultLimit = 100

export async function action({ request }: ActionArgs) {
  let userId = await requireUserId(request)

  let { action_name } = await zx.parseForm(request, {
    action_name: z.string(),
  })

  if (action_name === "delete") {
    let { id } = await zx.parseForm(request, {
      id: zx.NumAsString,
    })

    await prisma.question.delete({
      where: { id: id },
    })
  }

  return redirect("/query_manager/all")
}

export let loader: LoaderFunction = async ({
  params,
  request,
}): Promise<LoaderData> => {
  const userId = await requireUserId(request)
  const url = new URL(request.url)
  const limit = toNum(url.searchParams.get("limit") || defaultLimit)
  const offset = toNum(url.searchParams.get("offset") || 0)

  // store the query in the database
  const results = await prisma.question.findMany({
    // select: { id: true, question: true },
    select: {
      id: true,
      question: true,
      questionGroupId: true,
    },
    orderBy: { createdAt: "desc" },
    take: limit,
    skip: offset,
    where: { userId: userId },
  })

  const resultCount = await prisma.question.count({
    where: { userId: userId },
  })

  return {
    result: results,
    total: resultCount,
    limit: limit,
    offset: offset,
  }
}

export default function QueryAll() {
  const params = useParams()
  let data = useLoaderData<LoaderData>()
  const queries = data.result
  const total = data.total
  const navigate = useNavigate()

  const setPage = (pageNum: number) => {
    console.log("set page: ", pageNum)
    return navigate(
      `/query_manager/all?offset=${(pageNum - 1) * data.limit}&limit=${
        data.limit
      }`
    )
  }

  const queryRows = queries.map((query) => (
    <tr key={query.question}>
      <td>
        <Form method="post">
          <input type="hidden" name="id" value={query.id} />
          <input type="hidden" name="action_name" value="delete" />
          <Button type="submit">X</Button>
        </Form>
      </td>
      <td>
        <Link
          to={`/admin/${query.questionGroupId}/chart/raw?q=${query.question}`}
        >
          {query.question}
        </Link>
      </td>
    </tr>
  ))

  return (
    <Container size="lg">
      <Form method="post">
        <input type="hidden" name="action_name" value="train" />
        <Button type="submit">Train the Model</Button>
      </Form>
      <Table striped>
        <tbody>{queryRows}</tbody>
      </Table>
      <Pagination
        page={data.offset}
        onChange={setPage}
        total={total / data.limit}
      />
      ;
    </Container>
  )
}
