import type { DataTableColumn } from "mantine-datatable"
import { DataTable } from "mantine-datatable"
import { zx } from "zodix"

import type { ActionArgs, LoaderArgs } from "@remix-run/node"
import { json, redirect } from "@remix-run/node"
import {
  Form,
  Outlet,
  useFetcher,
  useLoaderData,
  useNavigate,
} from "@remix-run/react"

import { Box, Button, Grid } from "@mantine/core"
import { getHotkeyHandler, useHotkeys } from "@mantine/hooks"

import type { EvaluationQuestionGroup } from "@prisma/client"
import { EvaluationStatus } from "@prisma/client"

import { prisma } from "~/db.server"
import { requireUser } from "~/session.server"
import { isEmpty } from "~/utils"

export async function loader({ request, params }: LoaderArgs) {
  const user = await requireUser(request) // eslint-disable-line

  const evaluationGroups = await prisma.evaluationQuestionGroup.findMany({
    where: {
      status: EvaluationStatus.UNREAD, // TODO EvaluationStatus.INCOMPLETE],
    },
    include: {
      evaluationQuestions: {
        take: 3,
      },
    },
    orderBy: { createdAt: "desc" },
  })

  const { evaluationGroupId } = zx.parseParams(params, {
    evaluationGroupId: zx.NumAsString.optional(),
  })

  // TODO would be better to find the first group with questions, but this should be an edge case
  if (
    !evaluationGroupId &&
    evaluationGroups[0] &&
    !isEmpty(evaluationGroups[0].evaluationQuestions)
  ) {
    // TODO route helpers?!
    return redirect("/internal/group/" + evaluationGroups[0].id)
  }

  return json(evaluationGroups)
}

export async function action({ request }: ActionArgs) {
  // TODO create new evaluation group
  const user = await requireUser(request)

  const questionGroup = await prisma.evaluationQuestionGroup.create({
    data: {
      status: EvaluationStatus.UNREAD,
      dataSourceId: user.business!.dataSources[0].id,
    },
  })

  if (!questionGroup) {
    throw new Error("Failed to create question group")
  }

  return redirect("/internal/group/" + questionGroup.id)
}

export default function EvaluationGroupSelection({
  data,
}: {
  data: EvaluationQuestionGroup[]
}) {
  const evaluationGroupList = useLoaderData<
    typeof loader
  >() as unknown as EvaluationQuestionGroup[]

  const fetcher = useFetcher()
  const hotKeyConfig: any = [
    [
      "mod+Enter",
      () => {
        const formData = new FormData()
        fetcher.submit(formData, { method: "post" })
      },
    ],
  ]

  useHotkeys(hotKeyConfig)

  const navigate = useNavigate()
  const rowClick = (record: EvaluationQuestionGroup, recordIndex: number) => {
    navigate(record.id.toString(), { replace: true })
  }

  const dataColumns: DataTableColumn<EvaluationQuestionGroup>[] = [
    // TODO add summary of questions in the group column
    {
      accessor: "id",
      title: "Evaluation Groups",
      textAlignment: "right",
    },
  ]

  return (
    <Grid
      gutter={25}
      align="flex-start"
      onKeyDown={getHotkeyHandler(hotKeyConfig)}
    >
      <Grid.Col span={2}>
        <Form method="post">
          <Button type="submit" mb={15}>
            New Group ctrl+g
          </Button>
        </Form>
        <Box sx={{ height: "100%" }}>
          <DataTable
            striped
            highlightOnHover
            records={evaluationGroupList}
            columns={dataColumns}
            onRowClick={rowClick}
          />
        </Box>
      </Grid.Col>
      <Outlet />
    </Grid>
  )
}
