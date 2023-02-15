import invariant from "tiny-invariant"

import { json } from "@remix-run/node"
import { Link, useLoaderData } from "@remix-run/react"

import { Button, Grid, Table } from "@mantine/core"

import type { HistoryResult } from "~/lib/history.server"
import { getQuestionHistory } from "~/lib/history.server"
import { requireUser } from "~/session.server"

import { IconExternalLink } from "@tabler/icons-react"

export async function loader({ params, request }: LoaderArgs) {
  const user = await requireUser(request) // eslint-disable-line

  invariant(
    user.business?.dataSources.length == 1,
    "Only one data source supported"
  )

  const dataSource = user.business!.dataSources[0]
  const questionHistory = await getQuestionHistory(user.id, dataSource.id)

  return json(questionHistory)
}

const HistoryDisplayComponent = ({
  historyResult,
}: {
  historyResult: HistoryResult
}) => {
  const rows = historyResult.questionHistory.map((question) => (
    <tr key={question.id}>
      <td>{question.question}</td>
      <td>
        {new Date(question.createdAt).toLocaleDateString("en-US")} at{" "}
        {new Date(question.createdAt).toLocaleTimeString([], {
          timeStyle: "short",
        })}{" "}
        by {question.user.name}
      </td>
      <td>
        <Link
          target="_blank"
          to={`/question/${question.id}`}
          style={{ all: "unset" }}
        >
          <Button variant="subtle" rightIcon={<IconExternalLink size={16} />}>
            View
          </Button>
        </Link>
      </td>
    </tr>
  ))

  return (
    <Grid>
      <Grid.Col span={10} offset={1}>
        <Table verticalSpacing="sm">
          <thead>
            <tr>
              <th style={{ textAlign: "center", wordWrap: "break-word" }}>
                Question
              </th>
              <th style={{ textAlign: "center" }}>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </Table>
      </Grid.Col>
    </Grid>
  )
}

export default function HistoryIndexView() {
  const questionHistoryData = useLoaderData<typeof loader>() as HistoryResult

  //TODO: Add identify React DataTable component for searchable table
  //TODO: Add pagination to table with backend Prisma
  return (
    <>
      <HistoryDisplayComponent historyResult={questionHistoryData} />
    </>
  )
}
