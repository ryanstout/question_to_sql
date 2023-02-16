import { DataTable } from "mantine-datatable"
import invariant from "tiny-invariant"

import type { LoaderArgs } from "@remix-run/node"
import { json } from "@remix-run/node"
import { Link, useLoaderData } from "@remix-run/react"

import { Box, Button, Grid } from "@mantine/core"

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
  return (
    <Grid>
      <Grid.Col span={10} offset={1}>
        <Box sx={{ height: 450 }} mt={80}>
          <DataTable
            verticalSpacing="md"
            withBorder
            columns={[
              {
                accessor: "question",
                title: "Question History",
                textAlignment: "center",
              },
              {
                accessor: "Asked",
                textAlignment: "center",
                render: (record) => {
                  return `${new Date(record.createdAt).toLocaleDateString(
                    "en-US"
                  )} at ${new Date(record.createdAt).toLocaleTimeString([], {
                    timeStyle: "short",
                  })}`
                },
              },
              {
                accessor: "",
                textAlignment: "center",
                render: (record) => {
                  return (
                    <Link
                      target="_blank"
                      to={`/question/${record.id}`}
                      style={{ all: "unset" }}
                    >
                      <Button
                        variant="subtle"
                        rightIcon={<IconExternalLink size={16} />}
                      >
                        View
                      </Button>
                    </Link>
                  )
                },
              },
            ]}
            records={historyResult.questionHistory}
          />
        </Box>
      </Grid.Col>
    </Grid>
  )
}

export default function HistoryIndexView() {
  const questionHistoryData = useLoaderData<
    typeof loader
  >() as unknown as HistoryResult

  //TODO: Add searching for DataTable
  //TODO: Add pagination to table with backend Prisma

  return (
    <>
      <HistoryDisplayComponent historyResult={questionHistoryData} />
    </>
  )
}
