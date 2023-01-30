import { IconSearch } from "@tabler/icons"

import { Form } from "@remix-run/react"

import {
  Box,
  Flex,
  Loader,
  Paper,
  Text,
  TextInput,
  createStyles,
} from "@mantine/core"

const useStyles = createStyles((theme) => ({
  currentQuestionFeedback: {
    borderTop: 0,
    borderLeft: 4,
    borderRight: 0,
    borderBottom: 0,
    borderStyle: "solid",
    borderColor: theme.colors.indigo[7],
  },
}))

type QuestionState = {
  questionGroupId: string
  question: string
  previousQuestions: JSX.Element[]
  navigationState: string
}

const IS_ADMIN = false

export default function ConsoleSearch({
  currentQuestionState,
}: {
  currentQuestionState: QuestionState
}) {
  const { classes } = useStyles()

  return (
    <Box>
      <Form
        method="post"
        action={`/admin/${
          currentQuestionState.questionGroupId
        }?q=${encodeURIComponent(currentQuestionState.question)}`}
      >
        <Flex>
          <input
            type="hidden"
            name="questionGroupId"
            value={currentQuestionState.questionGroupId}
          />
          <TextInput
            size="lg"
            w="100%"
            name="q"
            placeholder="Enter a question about your business"
            icon={<IconSearch size={18} />}
            rightSection={
              currentQuestionState.navigationState === "submitting" ? (
                <Loader size="sm" />
              ) : (
                ""
              )
            }
          />
        </Flex>
      </Form>
      <Paper
        shadow="xs"
        p="md"
        my="xs"
        className={classes.currentQuestionFeedback}
      >
        <Text>{currentQuestionState.question}</Text>
      </Paper>
      {IS_ADMIN && (
        <Box sx={{ height: "90px", overflowY: "auto" }}>
          <Table p="sm">
            <tbody>{currentQuestionState.previousQuestions}</tbody>
          </Table>
        </Box>
      )}
    </Box>
  )
}
