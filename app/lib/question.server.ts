import invariant from "tiny-invariant"

import type { Question } from "@prisma/client"
import { FeedbackState } from "@prisma/client"

import { prisma } from "~/db.server"
import { isMockedPythonServer } from "~/lib/environment"
import { log } from "~/lib/logging"
import { pythonRequest, runQuery } from "~/lib/python.server"
import type { ResponseError } from "~/models/responseError.server"

import * as Sentry from "@sentry/remix"

export interface QuestionResult {
  question: Question
  status: "success" | "error"
  error?: ResponseError | null
  data: any[] | null
}

export async function getQuestionRecord(
  questionId: number,
  userId: number
): Promise<Question | null> {
  // TODO should this be scoped to DataSource id instead?
  return await prisma.question.findFirst({
    where: {
      AND: {
        id: {
          equals: questionId,
        },
        userId: {
          equals: userId,
        },
      },
    },
  })
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

  try {
    const targetSql =
      retrievedQuestionRecord.userSql || retrievedQuestionRecord.sql

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
    // TODO add error refinement here
    Sentry.captureException(e)

    // if snowflake is not responding properly, SQL is malformed and it's an invalid query
    retrievedQuestionRecord = await prisma.question.update({
      data: {
        feedbackState: FeedbackState.INVALID,
      },
      where: { id: questionId },
    })

    return {
      question: retrievedQuestionRecord,
      status: "error",
      error: {
        code: 500,
        message: "Error running query in Snowflake",
      },
      data: null,
    }
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

// creates a question, but does not get the results
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

  // TODO handle open AI failure here, although this is low pri since if `sql` is null, we can identify when openai fails
  const sql = await questionToSql(dataSourceId, question)
  log.debug("sql from python", { sql })

  questionRecord = await prisma.question.update({
    where: {
      id: questionRecord.id,
      // TODO should add user filter here
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
