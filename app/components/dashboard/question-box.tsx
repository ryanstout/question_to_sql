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

import type { Question } from "@prisma/client"

import { QuestionActions } from "~/routes/question/($questionId)"

import { IconSearch } from "@tabler/icons"

const useStyles = createStyles((theme) => ({
  lastQuestionDisplay: {
    border: 0,
    borderLeft: 4,
    borderStyle: "solid",
    borderColor: theme.colors.indigo[7],
  },
}))

export default function QuestionBox({
  questionRecord,
  isLoading,
}: {
  questionRecord?: Question
  isLoading: boolean
}) {
  const { classes } = useStyles()

  const [newQuestionText, setNewQuestionText] = useState(
    questionRecord?.question ?? ""
  )

  const [statefulQuestionRecord, setStatefulQuestionRecord] =
    useState<Question>(questionRecord)

  const [statefulIsLoading, setStatefulIsLoading] = useState(isLoading)

  useEffect(() => {
    if (questionRecord) {
      setStatefulQuestionRecord(questionRecord)
    }

    if (questionRecord && newQuestionText === "") {
      setNewQuestionText(questionRecord.question)
    }

    setStatefulIsLoading(isLoading)
  }, [questionRecord, isLoading, newQuestionText])

  return (
    <>
      <Form method="post">
        <input type="hidden" name="actionName" value={QuestionActions.CREATE} />
        <TextInput
          autoFocus
          autoComplete="off"
          size="lg"
          // w="100%"
          name="questionText"
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
      {statefulQuestionRecord && (
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
