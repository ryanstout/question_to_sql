import { useEffect, useState } from "react"

import { Form } from "@remix-run/react"

import {
  Button,
  Loader,
  Paper,
  Text,
  TextInput,
  createStyles,
} from "@mantine/core"

import type { EvaluationQuestion, Question } from "@prisma/client"

import { QuestionActions } from "~/routes/question/($questionId)"
import { isBlank } from "~/utils"

import { IconSearch } from "@tabler/icons"

const useStyles = createStyles((theme) => ({
  lastQuestionDisplay: {
    border: 0,
    borderLeft: 4,
    borderStyle: "solid",
    borderColor: theme.colors.indigo[7],
  },
}))

export const QUESTION_INPUT_NAME = "questionText"

export default function QuestionBox({
  questionRecord,
  isLoading,
  showPreviousQuestionDisplay = true,
}: {
  // TODO should really just create a supertype with just the question field
  questionRecord: Question | EvaluationQuestion | null
  isLoading: boolean
  showPreviousQuestionDisplay?: boolean
}) {
  const [newQuestionText, setNewQuestionText] = useState(
    questionRecord?.question ?? ""
  )
  const [statefulQuestionRecord, setStatefulQuestionRecord] =
    useState<typeof questionRecord>(questionRecord)
  const [statefulIsLoading, setStatefulIsLoading] = useState(isLoading)

  useEffect(() => {
    const newQuestionRecord =
      questionRecord && questionRecord.id != statefulQuestionRecord?.id

    if (questionRecord) {
      setStatefulQuestionRecord(questionRecord)
    }

    if (newQuestionRecord || (questionRecord && isBlank(newQuestionText))) {
      setNewQuestionText(questionRecord.question)
    }

    setStatefulIsLoading(isLoading)
  }, [questionRecord, isLoading, newQuestionText, statefulQuestionRecord?.id])

  const { classes } = useStyles()

  return (
    <>
      <Form method="post">
        <input type="hidden" name="actionName" value={QuestionActions.CREATE} />
        <TextInput
          autoFocus
          autoComplete="off"
          size="lg"
          disabled={statefulIsLoading}
          // TODO should use a constant for this
          name={QUESTION_INPUT_NAME}
          placeholder="Enter a question about your business"
          icon={<IconSearch size={18} />}
          value={newQuestionText}
          onChange={(e) => setNewQuestionText(e.currentTarget.value)}
          rightSectionWidth={statefulIsLoading ? 50 : 100}
          rightSection={
            statefulIsLoading ? (
              <Loader size="sm" />
            ) : (
              <Button type="submit">Search</Button>
            )
          }
        />
      </Form>
      {showPreviousQuestionDisplay && statefulQuestionRecord && (
        <Paper
          shadow="xs"
          p="md"
          my="xs"
          className={classes.lastQuestionDisplay}
        >
          <Text>{statefulQuestionRecord.question}</Text>
        </Paper>
      )}
    </>
  )
}
