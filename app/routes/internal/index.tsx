import type { DataTableColumn } from "mantine-datatable"
import { DataTable } from "mantine-datatable"
import { useEffect, useState } from "react"
import { z } from "zod"
import { zx } from "zodix"

import type { ActionArgs } from "@remix-run/node"
import { json } from "@remix-run/node"
import { useFetcher, useLoaderData } from "@remix-run/react"

import { Box, Button, Grid, Stack, Text, Title } from "@mantine/core"
import { getHotkeyHandler, useHotkeys } from "@mantine/hooks"
import { showNotification } from "@mantine/notifications"

import type { Question } from "@prisma/client"

import { prisma } from "~/db.server"
import f from "~/functional"
import { createEvaluationQuestionGroup } from "~/lib/evaluation-question.server"
import { requireAdmin } from "~/models/user.server"

export async function loader({ request }: ActionArgs) {
  const _user = await requireAdmin(request) // eslint-disable-line

  const questions = await prisma.question.findMany({
    distinct: ["question"],
    where: {
      // ensures the selected question does NOT have an evaluationQuestion associated
      evaluationQuestion: {
        none: {},
      },
    },
    orderBy: { createdAt: "desc" },
  })

  return json(questions)
}

// TODO should extract out as a separate component
// TODO https://discord.com/channels/854810300876062770/1073614244874043433/1073614244874043433
function RecordView({
  record,
  fields,
  header,
}: {
  record: Question
  // TODO should use a generic here...
  fields: (keyof Question)[]
  header: string
}) {
  return (
    <Stack justify="flex-start">
      <Title order={3}>{header}</Title>
      {fields.map((fieldName) => (
        <div key={fieldName}>
          <Title order={4}>{fieldName}</Title>
          <Text>{record[fieldName]?.toString() ?? <i>empty</i>}</Text>
        </div>
      ))}
    </Stack>
  )
}

export async function action({ request }: ActionArgs) {
  let { questions: questionIdList } = await zx.parseForm(request, {
    // TODO extract this out into a blog post + form helper
    questions: z.preprocess(
      // the list can come in as a string if there is only one item selected
      // https://stackoverflow.com/questions/74100894/how-to-transform-object-to-array-before-parsing-in-zod
      (v) => f.arrayWrap(v),
      zx.NumAsString.array().nonempty()
    ),
  })

  await createEvaluationQuestionGroup(questionIdList)

  return json({ ok: true })
}

function QuestionView({ question }: { question: Question }) {
  // TODO should be typed to input record type fields
  const displayFields: (keyof Question)[] = [
    "id",
    "question",
    "sql",
    "userSql",
    "feedbackState",
  ]

  return (
    <RecordView header="Question" record={question} fields={displayFields} />
  )
}

export default function EvaluationQuestionWizard() {
  const questionList = useLoaderData()
  const [selectedRecords, setSelectedRecords] = useState<Question[]>([])
  const fetcher = useFetcher()

  const createEvaluationGroup = () => {
    const formData = new FormData()
    selectedRecords.forEach((q) =>
      formData.append("questions", q.id.toString())
    )
    fetcher.submit(formData, { method: "post" })
  }

  useEffect(() => {
    if (fetcher.type === "done" && fetcher.data.ok) {
      showNotification({ message: "Evaluation Group Created" })
    }
  }, [fetcher])

  return (
    <>
      <QuestionSelection
        selectedRecords={selectedRecords}
        setSelectedRecords={setSelectedRecords}
        data={questionList}
        createEvaluationGroup={createEvaluationGroup}
      />
    </>
  )
}

export function QuestionSelection({
  data,
  createEvaluationGroup,
  selectedRecords,
  setSelectedRecords,
}: {
  data: Question[]
  // TODO this seems verbose, is there a better way to represent this?
  createEvaluationGroup: () => void
  selectedRecords: Question[]
  setSelectedRecords: (records: Question[]) => void
}) {
  const dataColumns: DataTableColumn<Question>[] = [
    {
      accessor: "id",
      title: "#",
      textAlignment: "right",
    },
    { accessor: "question" },
  ]
  const [detailRecord, setDetailRecord] = useState<Question | null>(null)

  const rowClick = (record: Question, recordIndex: number) => {
    setDetailRecord(record)
  }

  const canCreateGroup = selectedRecords.length > 0

  const hotKeyConfig: any = [
    [
      "mod+Enter",
      () => {
        if (canCreateGroup) {
          createEvaluationGroup()
        }
      },
    ],
  ]

  useHotkeys(hotKeyConfig)

  return (
    <Grid mb="md" align="flex-start" onKeyDown={getHotkeyHandler(hotKeyConfig)}>
      <Grid.Col xs={12} sm={6}>
        <Button
          onClick={createEvaluationGroup}
          mb={15}
          disabled={!canCreateGroup}
        >
          Create Evaluation Group ⌘+Enter
        </Button>
        <Box sx={{ height: "100%" }}>
          <DataTable
            withBorder
            borderRadius="sm"
            withColumnBorders
            striped
            highlightOnHover
            records={data}
            columns={dataColumns}
            onRowClick={rowClick}
            selectedRecords={selectedRecords}
            onSelectedRecordsChange={setSelectedRecords}
          />
        </Box>
      </Grid.Col>
      <Grid.Col xs={12} sm={6}>
        {detailRecord ? <QuestionView question={detailRecord} /> : null}
      </Grid.Col>
    </Grid>
  )
}
