import type { DataTableColumn } from "mantine-datatable"
import { DataTable } from "mantine-datatable"
import { $path } from "remix-routes"
import invariant from "tiny-invariant"
import { z } from "zod"
import { zx } from "zodix"

import type { ActionArgs, LoaderArgs } from "@remix-run/node"
import { json, redirect } from "@remix-run/node"
import { Form, useLoaderData } from "@remix-run/react"

import {
  ActionIcon,
  Button,
  Checkbox,
  Grid,
  Stack,
  Text,
  Textarea,
} from "@mantine/core"

import type {
  EvaluationQuestion,
  EvaluationQuestionGroup,
  Prisma,
} from "@prisma/client"

import DataDisplay from "~/components/dashboard/data-display"
import QuestionBox from "~/components/dashboard/question-box"
import SQLDisplay from "~/components/dashboard/sql-display"
import { FormActionName, useIsLoading } from "~/components/forms"
import f from "~/functional"
import evaluationQuestion, {
  loadEvaluationQuestionGroup,
} from "~/lib/evaluation-question.server"
import { log } from "~/lib/logging"

import { IconTrash } from "@tabler/icons-react"

type EvaluationQuestionGroupWithQuestionsAndDataSource =
  EvaluationQuestionGroup & {
    evaluationQuestions: EvaluationQuestion[]
    dataSource: { name: string }
  }

export async function loader({ params }: LoaderArgs) {
  const { evaluationGroupId } = zx.parseParams(params, {
    evaluationGroupId: zx.NumAsString,
  })

  const evaluationGroup = await loadEvaluationQuestionGroup(evaluationGroupId)

  return json(evaluationGroup)
}

async function parseActionName(request: Request) {
  const { actionName } = await zx.parseForm(request, {
    actionName: z.string(),
  })

  return actionName
}

enum EvaluationGroupActions {
  CREATE = "group_create",
  UPDATE = "group_update",
  FEEDBACK = "group_feedback",
  DELETE = "group_delete",
  DELETE_QUESTION = "group_delete_question",
}

export async function action({ request, params }: ActionArgs) {
  const actionName = await parseActionName(request)
  const { evaluationGroupId } = zx.parseParams(params, {
    evaluationGroupId: zx.NumAsString,
  })

  // TODO I don't know if using the same action enum here is best, but it will get this done faster

  if (actionName === EvaluationGroupActions.CREATE) {
    const { questionText } = await zx.parseForm(request, {
      questionText: z.string(),
    })

    await evaluationQuestion.createQuestion(evaluationGroupId, questionText)

    // at this point, a new question is asked, so we want to reload the current group UI
    return redirect(".")
  }

  // update the sql for a question
  if (actionName == EvaluationGroupActions.UPDATE) {
    log.info("updating sql of evaluation question")

    // TODO var names are weird since this is tied to the original UI, should refactor
    const { userSql: sql } = await zx.parseForm(request, {
      // TODO can we somehow validate against QUESTION_INPUT_NAME?
      userSql: z.string(),
    })

    await evaluationQuestion.updateQuestion(evaluationGroupId, sql)

    return redirect(".")
  }

  if (actionName === EvaluationGroupActions.FEEDBACK) {
    const { notes, assertionColumns } = await zx.parseForm(request, {
      notes: z.string().optional(),
      assertionColumns: z
        .preprocess(
          // the list can come in as a string if there is only one item selected
          // https://stackoverflow.com/questions/74100894/how-to-transform-object-to-array-before-parsing-in-zod
          (v) => f.arrayWrap(v),
          z.string().array()
        )
        .optional(),
    })

    await evaluationQuestion.markCorrect(
      evaluationGroupId,
      notes,
      assertionColumns
    )

    return redirect($path("/internal/group", {}))
  }

  if (actionName === EvaluationGroupActions.DELETE) {
    await evaluationQuestion.deleteQuestionGroup(evaluationGroupId)
    return redirect($path("/internal/group", {}))
  }

  // delete an individual question on a group
  if (actionName === EvaluationGroupActions.DELETE_QUESTION) {
    const { evaluationQuestionId } = await zx.parseForm(request, {
      evaluationQuestionId: zx.NumAsString,
    })

    await evaluationQuestion.deleteQuestion(evaluationQuestionId)
    return redirect(".")
  }

  throw new Error(`Invalid action ${actionName}`)
}

// display a list of columns in the JSON for
function ColumnSelectionDisplay({ results }: { results: Prisma.JsonValue }) {
  function columnNamesFromResults(results: any[]) {
    if (f.isEmpty(results)) {
      return []
    }

    const row = results[0]
    return Object.keys(row)
  }

  if (f.isNil(results)) {
    return <Text italic={true}>No results data</Text>
  }

  invariant(results instanceof Array, "results should always be an array")

  const columnNames = columnNamesFromResults(results)

  if (f.isEmpty(columnNames)) {
    return <Text italic={true}>No columns found</Text>
  }

  if (columnNames.length == 1) {
    return (
      <Text italic={true}>
        Only one column found, asserting against all columns by default
      </Text>
    )
  }

  return (
    <>
      <Text fw="bold">Columns</Text>
      {columnNames.map((row) => {
        return (
          <Checkbox
            name="assertionColumns"
            defaultChecked={true}
            value={row}
            label={row}
            key={row}
          />
        )
      })}
    </>
  )
}

export default function EvaluationGroupView() {
  const evaluationQuestionGroup = useLoaderData<
    typeof loader
  >() as unknown as EvaluationQuestionGroupWithQuestionsAndDataSource

  const dataColumns: DataTableColumn<
    (typeof evaluationQuestionGroup.evaluationQuestions)[0]
  >[] = [
    {
      accessor: "question",
      title: "Questions in Group",
      textAlignment: "right",
    },
    {
      accessor: "actions",
      title: "",
      textAlignment: "right",
      render: (question) => (
        <Form method="post">
          <FormActionName actionName={EvaluationGroupActions.DELETE_QUESTION} />
          <input
            type="hidden"
            name="evaluationQuestionId"
            value={question.id}
          />
          <ActionIcon color="red" type="submit">
            <IconTrash size={16} />
          </ActionIcon>
        </Form>
      ),
    },
  ]

  const lastQuestion =
    evaluationQuestionGroup.evaluationQuestions.at(-1) ?? null
  type lastQuestionType = NonNullable<typeof lastQuestion>

  const isLoading = useIsLoading()

  return (
    <>
      <Grid.Col span={3}>
        <Text mb={15}>
          {evaluationQuestionGroup.dataSource.name} #
          {evaluationQuestionGroup.dataSourceId}
        </Text>
        <DataTable<lastQuestionType>
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
            actionName={EvaluationGroupActions.CREATE}
          />
          <SQLDisplay
            isLoading={isLoading}
            sqlText={evaluationQuestionGroup.correctSql}
            actionName={EvaluationGroupActions.UPDATE}
          />
          <Form method="post">
            <FormActionName actionName={EvaluationGroupActions.FEEDBACK} />
            {/* TODO can we hint to the form that it shouldn't break the <stack/>? */}
            <Stack>
              <ColumnSelectionDisplay
                results={evaluationQuestionGroup.results}
              />
              <Button type="submit">Mark Correct ctrl+c</Button>
              <Text fw="bold">Notes</Text>
              <Textarea name="notes" />
            </Stack>
          </Form>
          <Form method="post">
            <FormActionName actionName={EvaluationGroupActions.DELETE} />
            <Button color="red" type="submit">
              Delete Evaluation Group
            </Button>
          </Form>
          <DataDisplay data={evaluationQuestionGroup.results} />
        </Stack>
      </Grid.Col>
    </>
  )
}

// TODO need to understand the difference between this and CatchBoundary
export function ErrorBoundary({ error }: { error: Error }) {
  return (
    <div>
      <h1>Error Loading Question Group</h1>
      <p>{error.message}</p>
      <p>The stack trace is:</p>
      <pre>{error.stack}</pre>
    </div>
  )
}
