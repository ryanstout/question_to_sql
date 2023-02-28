import invariant from "tiny-invariant"

import type { Question } from "@prisma/client"
import { FeedbackState } from "@prisma/client"

import { prisma } from "~/db.server"
import { isMockedPythonServer } from "~/lib/environment"
import { log } from "~/lib/logging"
import { pythonRequest, runQuery } from "~/lib/python.server"

import * as Sentry from "@sentry/remix"

export interface QuestionResult {
  question: Question
  status: "success" | "error"
  data: any[] | null
}

function throwIfNotPythonError(error: any) {
  if (error instanceof SyntaxError) {
    Sentry.captureException(error)
    return
  }

  throw error
}

async function updateQuestionStateAndReturnError(
  question: Question,
  state: FeedbackState
): Promise<QuestionResult> {
  const updatedQuestion = await prisma.question.update({
    where: {
      id: question.id,
    },
    data: {
      feedbackState: state,
    },
  })

  return {
    question: updatedQuestion,
    status: "error",
    data: null,
  }
}

// TODO we should probably just allow a questionn record to be passed
// if you have a question, and just want the results from the warehouse
export async function getResultsFromQuestion({
  questionRecord,
  questionId,
}: {
  questionRecord?: Question
  questionId?: number
}): Promise<QuestionResult> {
  let retrievedQuestionRecord: Question | null = null

  if (questionRecord) {
    retrievedQuestionRecord = questionRecord
  }

  if (!questionRecord && questionId) {
    retrievedQuestionRecord = await prisma.question.findFirst({
      where: {
        id: questionId,
      },
    })
  }

  invariant(retrievedQuestionRecord !== null, "question record not found")
  invariant(retrievedQuestionRecord.sql !== null, "sql is null")

  const targetSql =
    retrievedQuestionRecord.userSql || retrievedQuestionRecord.sql

  try {
    // this avoids making an additional request to openai
    const data = await runQuery(
      retrievedQuestionRecord.dataSourceId,
      targetSql,
      false
    )

    return {
      question: retrievedQuestionRecord,
      status: "success",
      data: data,
    }
  } catch (e: any) {
    throwIfNotPythonError(e)

    return await updateQuestionStateAndReturnError(
      retrievedQuestionRecord,
      FeedbackState.INVALID
    )
  }
}

// if the user wants to update the SQL directly
export async function updateQuestion(
  question: Question,
  userSql: string
): Promise<QuestionResult> {
  // updated SQL has been provided by the user, update the question record and
  // get updated results data

  const updateUser = await prisma.question.update({
    where: {
      // TODO should filter by user ID
      id: question.id,
    },
    data: {
      userSql: userSql,
    },
  })

  log.debug("sending updated query to snowflake")
  const results = await runQuery(question.dataSourceId, userSql, false)

  return {
    question: updateUser,
    status: "success",
    data: results,
  }
}

// creates a question, generates sql, but does not get the results
export async function createQuestion(
  userId: number,
  dataSourceId: number,
  question: string
): Promise<QuestionResult> {
  // create the question first, in case open AI fails
  let questionRecord = await prisma.question.create({
    data: {
      userId: userId,
      dataSourceId: dataSourceId,
      question: question,
    },
  })

  // we can identify when openai fails by empty sql, but setting the state directly is better
  let sql: string | null = null

  try {
    sql = await questionToSql(dataSourceId, question)
  } catch (e: any) {
    throwIfNotPythonError(e)

    return await updateQuestionStateAndReturnError(
      questionRecord,
      FeedbackState.UNGENERATED
    )
  }

  log.debug("generated sql", { sql })

  questionRecord = await prisma.question.update({
    where: {
      id: questionRecord.id,
    },
    data: {
      sql: sql,
    },
  })

  return {
    question: questionRecord,
    status: "success",
    data: null,
  }
}

export async function questionToSql(
  dataSourceId: number,
  naturalQuestion: string
): Promise<string> {
  // TODO remove me! Use mock server once we have a python API
  if (isMockedPythonServer()) {
    return Promise.resolve("SELECT * FROM ORDER LIMIT 10")
  }

  const response = await pythonRequest("/question", {
    data_source_id: dataSourceId,
    question: naturalQuestion,
  })

  return response["sql"]
}
