import invariant from "tiny-invariant"

import { LoaderArgs, json } from "@remix-run/node"
import { Link, useLoaderData } from "@remix-run/react"

import { Button, Grid, Table } from "@mantine/core"

import type { HistoryResult } from "~/lib/history.server"
import { getUserQuestionHistory } from "~/lib/history.server"
import { requireUser } from "~/session.server"

import { IconExternalLink } from "@tabler/icons-react"

export async function loader({ params, request }: LoaderArgs) {
  const user = await requireUser(request) // eslint-disable-line

  invariant(
    user.business?.dataSources.length == 1,
    "Only one data source supported"
  )

  const dataSource = user.business!.dataSources[0]
  const questionHistory = await getUserQuestionHistory(user.id, dataSource.id)

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
        })}
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
        <Table verticalSpacing="sm" mt={75}>
          <thead>
            <tr>
              <th style={{ wordWrap: "break-word", textAlign: "center" }}>
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
  const questionHistoryData = useLoaderData<
    typeof loader
  >() as unknown as HistoryResult

  //TODO: Use Mantine DataTable component for searchable table
  //TODO: Add pagination to table with backend Prisma

  return (
    <>
      <HistoryDisplayComponent historyResult={questionHistoryData} />
    </>
  )
}
