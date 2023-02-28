import { $path } from "remix-routes"
import invariant from "tiny-invariant"
import { z } from "zod"
import { zx } from "zodix"

import type { ActionArgs, LoaderArgs } from "@remix-run/node"
import { json, redirect } from "@remix-run/node"
import { useCatch, useLoaderData } from "@remix-run/react"

import { Accordion, Divider, Grid, Stack } from "@mantine/core"

import type { Question } from "@prisma/client"
import { FeedbackState } from "@prisma/client"

import DataDisplay from "~/components/dashboard/data-display"
import ErrorDisplay from "~/components/dashboard/error"
import QuestionActionHeader from "~/components/dashboard/question-action-header"
import QuestionBox from "~/components/dashboard/question-box"
import QuestionFeedback from "~/components/dashboard/question-feedback"
import SQLDisplay from "~/components/dashboard/sql-display"
import {
  parseActionName,
  parseQuestionText,
  useIsLoading,
} from "~/components/forms"
import { prisma } from "~/db.server"
import type { QuestionResult } from "~/lib/question.server"
import {
  createQuestion,
  getResultsFromQuestion,
  updateQuestion,
} from "~/lib/question.server"
import { requireUser } from "~/session.server"

import { IconPlus } from "@tabler/icons-react"

export enum QuestionActions {
  CREATE = "create",
  UPDATE = "update",
  FEEDBACK = "feedback",
  DELETE = "delete",
}

function abortOnBackendError(questionResults: QuestionResult) {
  if (questionResults.status === "error") {
    throw new Response("backend server error", {
      status: 500,
    })
  }
}

export async function action({ request }: ActionArgs) {
  const user = await requireUser(request)
  const dataSource = user.business!.dataSources[0]

  // create the query, attempt to load the generated sql if it doesn't exist,
  // then redirect to the query page

  const actionName = await parseActionName(request)

  if (actionName === QuestionActions.CREATE) {
    const questionText = await parseQuestionText(request)

    // this does not run the query on snowflake, this will happen on redirect
    const questionResult = await createQuestion(
      user.id,
      dataSource.id,
      questionText
    )

    abortOnBackendError(questionResult)

    return redirect(
      $path("/question/:questionId?", {
        questionId: questionResult.question.id,
      })
    )
  }

  // updating the usersql, updating the question text results in a new question
  if (actionName === QuestionActions.UPDATE) {
    const { questionId, userSql } = await zx.parseForm(request, {
      questionId: zx.NumAsString,
      userSql: z.string().trim(),
    })

    // TODO: figure out why multiple fields in where clauses on update
    // doesn't work, for now checking the question exists for the user
    // first
    const question = await prisma.question.findFirstOrThrow({
      where: {
        id: questionId,
        userId: user.id,
      },
    })

    const questionResult = await updateQuestion(question, userSql)

    abortOnBackendError(questionResult)

    return json(questionResult)
  }

  if (actionName === QuestionActions.FEEDBACK) {
    const { questionId, feedback } = await zx.parseForm(request, {
      questionId: zx.NumAsString,
      feedback: z.nativeEnum(FeedbackState),
    })

    let questionRecord = await prisma.question.findFirstOrThrow({
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

  const questionRecord = await prisma.question.findFirstOrThrow({
    where: {
      userId: user.id,
      id: questionId,
    },
  })

  // TODO we should handle pulling question record consistently and present a 404, need a helper for this
  // if (!questionRecord) {
  //   throw new Response("Question not found", { status: 404 })
  // }

  const questionResults = await getResultsFromQuestion({ questionRecord })

  abortOnBackendError(questionResults)

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

export default function QuestionView() {
  // TODO https://github.com/remix-run/remix/issues/3931
  const questionResult = useLoaderData<
    typeof loader
  >() as unknown as QuestionResult | null

  const questionRecord = questionResult?.question ?? null
  const isLoading = useIsLoading()

  // TODO I don't get why we are using a grid here, a simple stack should work fine?
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
            {!questionRecord ? null : (
              <>
                <SQLResultComponent
                  isLoading={isLoading}
                  questionRecord={questionRecord}
                />
                <QuestionFeedback questionRecord={questionRecord} />
              </>
            )}
          </Stack>
        </Grid.Col>
      </Grid>
      {!questionRecord ? null : (
        <>
          <Divider my="md" variant="dotted" />
          <Grid>
            <Grid.Col span={10} offset={1}>
              <DataDisplay data={questionResult?.data ?? null} />
            </Grid.Col>
          </Grid>
        </>
      )}
    </>
  )
}

// TODO do we know if errors are sent to sentry if this hit these boundaries? Need to investigate how they work further

export function CatchBoundary() {
  const caught = useCatch()
  const errorProps = {
    returnLink: "/question",
    returnLinkText: "New Question",
    userMessage:
      "We encountered an unexpected error. Please try a new question!",
  }

  if (caught.status === 500) {
    errorProps.userMessage =
      "Mea Culpa! There was an error retrieving your results. Our team will investigate and reach out when we have your answer!"
  }

  if (caught.status === 404) {
    errorProps.userMessage =
      "We couldn't find this question. Please ask a new question instead!"
  }

  return <ErrorDisplay {...errorProps} />
}

export function ErrorBoundary({ error }: { error: Error }) {
  return <div>An error ocurred.</div>
}
