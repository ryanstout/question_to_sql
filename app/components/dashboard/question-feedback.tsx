import { useEffect } from "react"

import { Form } from "@remix-run/react"

import { Box, Button, Center, Flex, Grid, Text } from "@mantine/core"

import type { Question } from "@prisma/client"
import { FeedbackState } from "@prisma/client"

import { FormActionName } from "~/routes/internal/group/$evaluationGroupId"
import { QuestionActions } from "~/routes/question/($questionId)"

import { IconCheck, IconFlag } from "@tabler/icons-react"

export default function QuestionFeedback({
  questionRecord,
}: {
  questionRecord: Question | null
}) {
  useEffect(() => {}, [questionRecord])

  if (!questionRecord) {
    return <></>
  }

  if (
    questionRecord.feedbackState === FeedbackState.CORRECT ||
    questionRecord.feedbackState === FeedbackState.INCORRECT
  ) {
    return (
      <Center>
        <Text color="blue">
          <i>Feedback provided</i> <IconCheck size={14} />
        </Text>
      </Center>
    )
  }

  const commonFormInputs = (
    <>
      <FormActionName actionName={QuestionActions.FEEDBACK} />
      <input type="hidden" name="questionId" value={questionRecord.id} />
    </>
  )

  return (
    <Grid>
      <Grid.Col span={10} offset={1}>
        <Center>
          <Flex>
            <Box pr="25px">
              <Form method="post">
                {commonFormInputs}
                <input
                  type="hidden"
                  name="feedback"
                  value={FeedbackState.CORRECT}
                />
                <Button
                  leftIcon={<IconCheck size={16} />}
                  type="submit"
                  color="teal"
                  variant="filled"
                >
                  Mark Correct
                </Button>
              </Form>
            </Box>
            <Box>
              <Form method="post">
                <input
                  type="hidden"
                  name="feedback"
                  value={FeedbackState.INCORRECT}
                />
                {commonFormInputs}
                <Button
                  leftIcon={<IconFlag size={16} />}
                  type="submit"
                  color="red"
                  variant="outline"
                >
                  Mark Incorrect
                </Button>
              </Form>
            </Box>
          </Flex>
        </Center>
      </Grid.Col>
    </Grid>
  )
}
