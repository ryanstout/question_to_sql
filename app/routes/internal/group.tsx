import type { DataTableColumn } from "mantine-datatable"
import { DataTable } from "mantine-datatable"
import { useEffect, useState } from "react"
import { $path } from "remix-routes"
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

import { Box, Button, Checkbox, Grid, Text } from "@mantine/core"
import { getHotkeyHandler, useHotkeys } from "@mantine/hooks"

import type {
  EvaluationQuestion,
  EvaluationQuestionGroup,
} from "@prisma/client"
import { EvaluationStatus } from "@prisma/client"

import * as evaluationQuestion from "~/lib/evaluation-question.server"
import { prisma } from "~/db.server"
import f from "~/functional"
import { requireAdmin } from "~/models/user.server"
import { requireUser } from "~/session.server"

const QUESTION_PREVIEW_LIMIT = 3

export async function loader({ request, params }: LoaderArgs) {
  const _user = await requireAdmin(request) // eslint-disable-line

  const evaluationGroups = await prisma.evaluationQuestionGroup.findMany({
    include: {
      evaluationQuestions: {
        take: QUESTION_PREVIEW_LIMIT,
      },
    },
    orderBy: { createdAt: "desc" },
  })

  const { evaluationGroupId } = zx.parseParams(params, {
    evaluationGroupId: zx.NumAsString.optional(),
  })

  const firstUnansweredEvaluationGroupWithQuestions = evaluationGroups.find(
    (group) =>
      group.status !== EvaluationStatus.CORRECT &&
      !f.isEmpty(group.evaluationQuestions)
  )
  // TODO would be better to find the first group with questions, but this should be an edge case
  if (!evaluationGroupId && firstUnansweredEvaluationGroupWithQuestions) {
    return redirect(
      $path("/internal/group/:evaluationGroupId", {
        evaluationGroupId: firstUnansweredEvaluationGroupWithQuestions.id,
      })
    )
  }

  return json(evaluationGroups)
}

export async function action({ request }: ActionArgs) {
  const user = await requireUser(request)
  const dataSource = user.business!.dataSources[0]

  const questionGroup =
    await evaluationQuestion.createBlankEvaluationQuestionGroup(dataSource.id)

  // TODO since this is a redirect, we need to use a flash cookie
  return redirect(
    // TODO 3rd arg is annoying this needs to be fixed when the underlying library is fixed
    $path("/internal/group/:evaluationGroupId", {
      evaluationGroupId: questionGroup.id,
    })
  )
}

export default function EvaluationGroupSelection() {
  type EvaluationQuestionGroupWithQuestions = EvaluationQuestionGroup & {
    evaluationQuestions: EvaluationQuestion[]
  }

  const evaluationGroupList = useLoaderData<
    typeof loader
    // TODO this is worse than most; waiting on a remix bug to fix
  >() as unknown as EvaluationQuestionGroupWithQuestions[]

  const [excludeCompletedGroups, setExcludeCompletedGroups] = useState(true)
  const [filteredEvaluationGroupList, setFilteredEvaluationGroupList] =
    useState(evaluationGroupList)

  // create a new group on hotkey shortcut
  const fetcher = useFetcher()
  // TODO any is used because the hotkey library doesn't have the correct types; check again later
  const hotKeyConfig: any = [
    [
      "mod+Enter",
      () => {
        fetcher.submit(null, { method: "post" })
      },
    ],
  ]
  useHotkeys(hotKeyConfig)

  useEffect(() => {
    const filteredList = evaluationGroupList.filter(
      (group) =>
        !excludeCompletedGroups || group.status !== EvaluationStatus.CORRECT
    )
    setFilteredEvaluationGroupList(filteredList)
  }, [excludeCompletedGroups, evaluationGroupList])

  const navigate = useNavigate()
  const rowClick = (record: EvaluationQuestionGroup, recordIndex: number) => {
    navigate(record.id.toString(), { replace: true })
  }

  const dataColumns: DataTableColumn<(typeof evaluationGroupList)[0]>[] = [
    // TODO add summary of questions in the group column
    {
      accessor: "id",
      title: "Evaluation Groups",
      textAlignment: "right",
      render: (record) => {
        const questionString = record.evaluationQuestions
          .map((q) => q.question)
          .slice(0, QUESTION_PREVIEW_LIMIT)
          .join(", ")

        const isCorrect = record.status === EvaluationStatus.CORRECT
        const rowDisplay = f.isEmpty(questionString) ? (
          <i>No questions</i>
        ) : (
          questionString
        )

        if (isCorrect) {
          return <Text color="green">{questionString}</Text>
        } else {
          return rowDisplay
        }
      },
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
            New Group cmd+enter
          </Button>
        </Form>
        <Checkbox
          mb={15}
          label="Exclude completed groups"
          checked={excludeCompletedGroups}
          onChange={(e) => setExcludeCompletedGroups(e.currentTarget.checked)}
        />
        <Box sx={{ height: "100%" }}>
          <DataTable
            minHeight={150}
            striped
            highlightOnHover
            records={filteredEvaluationGroupList}
            columns={dataColumns}
            onRowClick={rowClick}
          />
        </Box>
      </Grid.Col>
      <Outlet />
    </Grid>
  )
}
