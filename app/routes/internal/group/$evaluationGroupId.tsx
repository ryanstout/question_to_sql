import type { DataTableColumn } from "mantine-datatable"
import { DataTable } from "mantine-datatable"
import { z } from "zod"
import { zx } from "zodix"

import type { ActionArgs, LoaderArgs } from "@remix-run/node"
import { json, redirect } from "@remix-run/node"
import {
  Form,
  useLoaderData,
  useNavigation,
  useTransition,
} from "@remix-run/react"

import { Button, Grid, Stack, Text, Textarea } from "@mantine/core"

import type {
  EvaluationQuestion,
  EvaluationQuestionGroup,
} from "@prisma/client"

import DataDisplay from "~/components/dashboard/data-display"
import QuestionBox from "~/components/dashboard/question-box"
import SQLDisplay from "~/components/dashboard/sql-display"
import { prisma } from "~/db.server"
import evaluationQuestion from "~/lib/evaluation-question.server"
import { log } from "~/lib/logging.server"
import { questionToSql, runQuery } from "~/lib/question.server"
import { QuestionActions } from "~/routes/question/($questionId)"
import { isBlank, isEmpty } from "~/utils"

type EvaluationQuestionGroupWithQuestions = EvaluationQuestionGroup & {
  evaluationQuestions: EvaluationQuestion[]
}

export async function loader({ params }: LoaderArgs) {
  const { evaluationGroupId } = zx.parseParams(params, {
    evaluationGroupId: zx.NumAsString,
  })

  let evaluationGroup = await prisma.evaluationQuestionGroup.findUniqueOrThrow({
    where: { id: evaluationGroupId },
    include: { evaluationQuestions: true },
  })

  const lastQuestion = evaluationGroup.evaluationQuestions.at(-1)

  // if no correctSql exists, generate it
  if (lastQuestion && isBlank(evaluationGroup.correctSql)) {
    log.info("generating sql for evaluation question group")

    const generatedSql = await questionToSql(
      evaluationGroup.dataSourceId,
      lastQuestion.question
    )

    evaluationGroup = await prisma.evaluationQuestionGroup.update({
      where: { id: evaluationGroupId },
      data: { correctSql: generatedSql },
      // TODO this is inefficient, but it avoids having to manage model state right now
      include: { evaluationQuestions: true },
    })
  }

  if (evaluationGroup.correctSql && isEmpty(evaluationGroup.results)) {
    log.info("result cache empty, generating")

    const results = await runQuery(
      evaluationGroup.dataSourceId,
      evaluationGroup.correctSql
    )

    evaluationGroup = await prisma.evaluationQuestionGroup.update({
      where: { id: evaluationGroupId },
      data: { results },
      // TODO this is inefficient, but it avoids having to manage model state right now
      include: { evaluationQuestions: true },
    })
  }

  return json(evaluationGroup)
}

async function parseActionName(request: Request) {
  const { actionName } = await zx.parseForm(request, {
    actionName: z.string(),
  })

  return actionName
}

export async function action({ request, params }: ActionArgs) {
  const actionName = await parseActionName(request)
  let { evaluationGroupId } = zx.parseParams(params, {
    evaluationGroupId: zx.NumAsString,
  })

  // TODO I don't know if using the same action enum here is best, but it will get this done faster

  if (actionName === QuestionActions.CREATE) {
    const { questionText } = await zx.parseForm(request, {
      questionText: z.string(),
    })

    await evaluationQuestion.createQuestion(evaluationGroupId, questionText)

    // at this point, a new question is asked, so we want to reload the current group UI
    return redirect(".")
  }

  // update the sql for a question
  if (actionName == QuestionActions.UPDATE) {
    log.info("updating sql of evaluation question")
    // TODO var names are weird since this is tied to the original UI, should refactor
    const { userSql: sql } = await zx.parseForm(request, {
      // TODO can we somehow validate against QUESTION_INPUT_NAME?
      userSql: z.string(),
    })

    await evaluationQuestion.updateQuestion(evaluationGroupId, sql)

    return redirect(".")
  }

  if (actionName === QuestionActions.FEEDBACK) {
    const { notes } = await zx.parseForm(request, {
      notes: z.string().optional(),
    })

    await evaluationQuestion.markCorrect(evaluationGroupId, notes)

    return redirect(`/internal/group`)
  }

  throw new Error("Invalid action")
}

// TODO extract out and use anywhere we use the `actionName` pattern
export function FormActionName({ actionName }: { actionName: string }) {
  return <input type="hidden" name="actionName" value={actionName} />
}

// TODO is this a good pattern? not sure. It definitely needs a different name
function useLoading() {
  const transition = useTransition()
  const navigation = useNavigation()
  const isLoading =
    navigation.state == "submitting" || transition.state != "idle"
  return isLoading
}

export default function EvaluationGroupView() {
  const evaluationQuestionGroup = useLoaderData<
    typeof loader
  >() as unknown as EvaluationQuestionGroupWithQuestions

  const dataColumns: DataTableColumn<
    (typeof evaluationQuestionGroup.evaluationQuestions)[0]
  >[] = [
    {
      accessor: "question",
      title: "Questions in Group",
      textAlignment: "right",
    },
    // { accessor: "question" },
  ]

  const lastQuestion =
    evaluationQuestionGroup.evaluationQuestions.at(-1) ?? null
  const isLoading = useLoading()

  return (
    <>
      <Grid.Col span={3}>
        <Text>TODO Datasource/User display</Text>
        <DataTable<(typeof evaluationQuestionGroup.evaluationQuestions)[0]>
          striped
          records={evaluationQuestionGroup.evaluationQuestions}
          columns={dataColumns}
        />
      </Grid.Col>
      <Grid.Col span={7}>
        <Stack>
          <QuestionBox
            isLoading={isLoading}
            showPreviousQuestionDisplay={false}
            questionRecord={lastQuestion}
          />
          <SQLDisplay
            isLoading={isLoading}
            sqlText={evaluationQuestionGroup.correctSql}
          />
          <Form method="post">
            <FormActionName actionName={QuestionActions.FEEDBACK} />
            {/* TODO can we hint to the form that it shouldn't break the stack? */}
            <Stack>
              <Button type="submit">Mark Correct ctrl+c</Button>
              <Text fw="bold">Notes</Text>
              <Textarea name="notes" />
            </Stack>
          </Form>
          <DataDisplay data={evaluationQuestionGroup.results} />
        </Stack>
      </Grid.Col>
    </>
  )
}
