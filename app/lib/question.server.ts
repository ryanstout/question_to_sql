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
  try {
    // TODO should we scope this to DataSource instead of user?
    const questionRecord = await prisma.question.findFirstOrThrow({
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

    return questionRecord
  } catch (e: any) {
    return null
  }
}

// if you have a question, and just want the results from the warehouse
export async function getResultsFromQuestion({
  questionRecord,
}: {
  questionRecord?: Question
}): Promise<QuestionResult> {
  let retrievedQuestionRecord: Question | null = null

  if (questionRecord) {
    retrievedQuestionRecord = questionRecord
  }

  invariant(retrievedQuestionRecord !== null, "question record not found")
  invariant(retrievedQuestionRecord.sql !== null, "sql is null")

  try {
    const targetSql =
      retrievedQuestionRecord.userSql || retrievedQuestionRecord.sql

    // this avoids making an additional request to openai
    const data = await runQuery(retrievedQuestionRecord.dataSourceId, targetSql)

    return {
      question: retrievedQuestionRecord,
      status: "success",
      data: data,
    }
  } catch (e: any) {
    Sentry.captureException(e)

    // if snowflake is not responding properly, SQL is malformed and it's an invalid query
    retrievedQuestionRecord = await prisma.question.update({
      data: {
        feedbackState: FeedbackState.INVALID,
      },
      where: { id: questionRecord?.id },
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
      id: question.id,
    },
    data: {
      userSql: userSql,
    },
  })

  log.debug("sending updated query to snowflake")
  const results = await runQuery(question.dataSourceId, userSql)

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

  // TODO handle open AI failure here
  const sql = await questionToSql(dataSourceId, question)
  log.debug("sql from python", { sql })

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
    return new Promise((resolve, reject) => {
      resolve("SELECT * FROM ORDER LIMIT 10")
    })
  }

  const response = await pythonRequest("question", {
    data_source_id: dataSourceId,
    question: naturalQuestion,
  })

  return response["sql"]
}
