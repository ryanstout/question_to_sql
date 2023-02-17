import { useEffect } from "react"
import invariant from "tiny-invariant"
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

import {
  Accordion,
  Box,
  Button,
  Center,
  Divider,
  Flex,
  Grid,
  Stack,
  Text,
} from "@mantine/core"

import type { Question } from "@prisma/client"
import { FeedbackState } from "@prisma/client"

import DataDisplay from "~/components/dashboard/data-display"
import QuestionActionHeader from "~/components/dashboard/question-action-header"
import QuestionBox from "~/components/dashboard/question-box"
import SQLDisplay from "~/components/dashboard/sql-display"
import { prisma } from "~/db.server"
import type { QuestionResult } from "~/lib/question.server"
import {
  createQuestion,
  getResultsFromQuestion,
  updateQuestion,
} from "~/lib/question.server"
import { requireUser } from "~/session.server"

import { IconCheck, IconFlag, IconPlus } from "@tabler/icons-react"

export enum QuestionActions {
  CREATE = "create",
  UPDATE = "update",
  FEEDBACK = "feedback",
}

export async function action({ request }: ActionArgs) {
  const user = await requireUser(request)

  invariant(
    user.business?.dataSources.length == 1,
    "Only one data source supported"
  )

  const dataSource = user.business!.dataSources[0]

  // create the query, attempt to load the generated sql if it doesn't exist,
  // then redirect to the query page
  // NOTE: q may get put in the url also, but needs to come from the form first
  const { actionName } = await zx.parseForm(request, {
    actionName: z.nativeEnum(QuestionActions),
  })

  if (actionName === QuestionActions.CREATE) {
    const { questionText } = await zx.parseForm(request, {
      questionText: z.string(),
    })

    // this does not run the query on snowflake, this will happen on redirect
    const questionRecord = await createQuestion(
      user.id,
      dataSource.id,
      questionText
    )

    // TODO shouldn't there be helpers for the route strings? Did we forget everything we learned from rails?
    return redirect(`/question/${questionRecord.question.id}`)
  }

  // updating the usersql, updating the question text results in a new question
  if (actionName === QuestionActions.UPDATE) {
    const { questionId, userSql } = await zx.parseForm(request, {
      questionId: zx.NumAsString,
      userSql: z.string(),
    })

    // TODO: figure out why multiple fields in where clauses on update
    // doesn't work, for now checking the question exists for the user
    // first
    const question = await prisma.question.findFirst({
      where: {
        id: questionId,
        userId: user.id,
      },
    })

    invariant(question, "Unable to find question")

    const questionResult = await updateQuestion(question, userSql)

    return json(questionResult)
  }

  if (actionName === QuestionActions.FEEDBACK) {
    const { questionId, feedback } = await zx.parseForm(request, {
      questionId: zx.NumAsString,
      feedback: z.nativeEnum(FeedbackState),
    })

    let questionRecord = await prisma.question.findFirst({
      where: {
        userId: user.id,
        id: questionId,
      },
    })

    invariant(questionRecord, "Unable to find question")

    // TODO we should check if feedback has already been given, this should be an invalid state
    //      however, this is something that should be validated on the model level... but this is a terrible ORM

    questionRecord = await prisma.question.update({
      data: {
        feedbackState: feedback,
      },
      where: { id: questionRecord.id },
    })

    const questionResult: QuestionResult = {
      question: questionRecord,
      status: "success",
      data: null,
    }

    return json(questionResult)
  }
}

export async function loader({ params, request }: LoaderArgs) {
  const user = await requireUser(request) // eslint-disable-line

  // TODO missing fields in params seem to return a terrible ambiguous error to the FE...
  const { questionId } = zx.parseParams(params, {
    // optional because this page can be used *without* a question ID if the user is asking a net-new question
    questionId: zx.NumAsString.optional(),
  })

  if (!questionId) {
    return null
  }

  // TODO should validate the user actually has access to this question!
  const questionResults = await getResultsFromQuestion({ questionId })

  return json(questionResults)
}

function SQLResultComponent({
  isLoading,
  questionRecord,
}: {
  isLoading: boolean
  questionRecord: Question | null
}) {
  return (
    <Accordion
      chevron={<IconPlus size={16} />}
      styles={{
        item: {
          // styles added to all items
          backgroundColor: "#fff",
          border: "1px solid #ededed",
        },
        chevron: {
          "&[data-rotate]": {
            transform: "rotate(45deg)",
          },
        },
      }}
    >
      <Accordion.Item value="sqlResultDisplay">
        <Accordion.Control>View SQL Statement</Accordion.Control>
        <Accordion.Panel p="sm">
          <SQLDisplay
            sqlText={questionRecord?.userSql ?? questionRecord?.sql ?? null}
            additionalFields={
              <input
                type="hidden"
                name="questionId"
                value={questionRecord?.id}
              />
            }
            isLoading={isLoading}
          />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  )
}

function FeedbackComponent({
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
      <input type="hidden" name="actionName" value={QuestionActions.FEEDBACK} />
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

export default function QuestionView() {
  // TODO https://github.com/remix-run/remix/issues/3931
  const questionResult = useLoaderData<
    typeof loader
  >() as unknown as QuestionResult | null

  const questionRecord = questionResult?.question ?? null

  const transition = useTransition()
  const navigation = useNavigation()
  const isLoading =
    navigation.state == "submitting" || transition.state != "idle"

  return (
    <>
      <Grid>
        <Grid.Col span={8} offset={2} p="lg">
          <Stack mr={30}>
            <QuestionActionHeader
              isLoading={isLoading}
              questionResult={questionResult}
            />
            <QuestionBox
              isLoading={isLoading}
              questionRecord={questionRecord}
            />
            <SQLResultComponent
              isLoading={isLoading}
              questionRecord={questionRecord}
            />
            <FeedbackComponent questionRecord={questionRecord} />
          </Stack>
        </Grid.Col>
      </Grid>
      <Divider my="md" variant="dotted" />
      <Grid>
        <Grid.Col span={10} offset={1}>
          <DataDisplay data={questionResult?.data ?? null} />
        </Grid.Col>
      </Grid>
    </>
  )
}
