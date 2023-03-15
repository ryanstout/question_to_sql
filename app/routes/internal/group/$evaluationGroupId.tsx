import type { DataTableColumn } from "mantine-datatable"
import { DataTable } from "mantine-datatable"
import { $path } from "remix-routes"
import invariant from "tiny-invariant"
import { z } from "zod"
import { zx } from "zodix"

import type { ActionArgs, LoaderArgs } from "@remix-run/node"
import { json, redirect } from "@remix-run/node"
import { Form, useFetcher, useLoaderData } from "@remix-run/react"

import {
  ActionIcon,
  Button,
  Center,
  Checkbox,
  Grid,
  Stack,
  Text,
  Textarea,
  createStyles,
} from "@mantine/core"
import { useInputState } from "@mantine/hooks"

import type {
  EvaluationQuestion,
  EvaluationQuestionGroup,
  Prisma,
} from "@prisma/client"

import * as evaluationQuestion from "~/lib/evaluation-question.server"
import DataDisplay from "~/components/dashboard/data-display"
import QuestionBox from "~/components/dashboard/question-box"
import SQLDisplay from "~/components/dashboard/sql-display"
import {
  ACTION_NAME_LABEL,
  FormActionName,
  parseActionName,
  parseQuestionText,
  useIsLoading,
} from "~/components/forms"
import f from "~/functional"
import { log } from "~/lib/logging"

import { IconTrash } from "@tabler/icons-react"

const useStyles = createStyles((theme) => ({
  columnDivider: {
    border: 0,
    borderLeft: 1,
    borderStyle: "solid",
    borderColor: theme.colors.gray[3],
  },
}))

type EvaluationQuestionGroupWithQuestionsAndDataSource =
  EvaluationQuestionGroup & {
    evaluationQuestions: EvaluationQuestion[]
    dataSource: { name: string }
  }

export async function loader({ params }: LoaderArgs) {
  const { evaluationGroupId } = zx.parseParams(params, {
    evaluationGroupId: zx.NumAsString,
  })

  const evaluationGroup = await evaluationQuestion.loadEvaluationQuestionGroup(
    evaluationGroupId
  )

  return json(evaluationGroup)
}

enum EvaluationGroupActions {
  CREATE = "group_create",
  UPDATE = "group_update",
  UPDATE_NOTES = "group_update_notes",
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
    const questionText = await parseQuestionText(request)
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

    return redirect($path("/internal/group"))
  }

  if (actionName === EvaluationGroupActions.DELETE) {
    await evaluationQuestion.deleteQuestionGroup(evaluationGroupId)
    return redirect($path("/internal/group"))
  }

  // delete an individual question on a group
  if (actionName === EvaluationGroupActions.DELETE_QUESTION) {
    const { evaluationQuestionId } = await zx.parseForm(request, {
      evaluationQuestionId: zx.NumAsString,
    })

    await evaluationQuestion.deleteQuestion(
      evaluationQuestionId,
      evaluationGroupId
    )
    return redirect(".")
  }

  if (actionName === EvaluationGroupActions.UPDATE_NOTES) {
    const { notes } = await zx.parseForm(request, {
      notes: z.string(),
    })

    await evaluationQuestion.updateNotes(evaluationGroupId, notes)

    return redirect(".")
  }

  throw new Error(`Invalid action ${actionName}`)
}

// display a list of columns in the JSON to select which ones are significant
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
  // TODO https://github.com/remix-run/remix/issues/3931
  const evaluationQuestionGroup = useLoaderData<
    typeof loader
  >() as unknown as EvaluationQuestionGroupWithQuestionsAndDataSource

  const lastQuestion =
    evaluationQuestionGroup.evaluationQuestions.at(-1) ?? null
  type lastQuestionType = NonNullable<typeof lastQuestion>

  const dataColumns: DataTableColumn<lastQuestionType>[] = [
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
            // TODO using strings for this feels weird, there's got to be a better way to type this
            name="evaluationQuestionId"
            value={question.id}
          />
          <ActionIcon color="red" type="submit">
            <IconTrash size={18} />
          </ActionIcon>
        </Form>
      ),
    },
  ]

  const isLoading = useIsLoading()
  const [notes, setNotes] = useInputState(evaluationQuestionGroup.notes ?? "")

  const notesFetcher = useFetcher()
  function updateNotes(event: React.ChangeEvent<HTMLTextAreaElement>) {
    notesFetcher.submit(
      {
        [ACTION_NAME_LABEL]: EvaluationGroupActions.UPDATE_NOTES,
        notes,
      },
      {
        method: "post",
      }
    )
  }

  const { classes } = useStyles()

  return (
    <>
      <Grid.Col span={3} className={classes.columnDivider}>
        <Text mb={15}>
          <Center>
            DataSource: {evaluationQuestionGroup.dataSource.name} #
            {evaluationQuestionGroup.dataSourceId}
          </Center>
        </Text>
        <DataTable<lastQuestionType>
          minHeight={150}
          striped
          records={evaluationQuestionGroup.evaluationQuestions}
          columns={dataColumns}
        />
      </Grid.Col>
      <Grid.Col
        // include `id` to force a complete rerender when the group changes
        // https://stackoverflow.com/questions/75317212/remix-run-how-to-reload-all-child-components-of-a-component-loaded-through-an
        key={evaluationQuestionGroup.id}
        span={7}
        className={classes.columnDivider}
      >
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
              <Textarea
                disabled={isLoading}
                onBlur={updateNotes}
                value={notes}
                onChange={setNotes}
                name="notes"
              />
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
