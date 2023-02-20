import invariant from "tiny-invariant"

import type { Question } from "@prisma/client"

import { prisma } from "~/db.server"
import { isMockedPythonServer } from "~/lib/environment"
import { log } from "~/lib/logging"
import { pythonRequest, runQuery } from "~/lib/python.server"
import type { ResponseError } from "~/models/responseError.server"

export interface QuestionResult {
  question: Question
  status: "success" | "error"
  error?: ResponseError | null
  data: any[] | null
}

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

  try {
    invariant(retrievedQuestionRecord !== null, "question record not found")
    invariant(retrievedQuestionRecord.sql !== null, "sql is null")

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
    // TODO is there a better way to check for Invariant error than this specific string message?
    // TODO should we catch null sql error specifically?

    if (e.message === "Invariant failed: question record not found") {
      return {
        question: retrievedQuestionRecord || ({} as Question),
        status: "error",
        error: {
          code: 404,
          message: "Question not found",
        },
        data: [],
      }
    }

    return {
      question: retrievedQuestionRecord || ({} as Question),
      status: "error",
      error: {
        code: 500,
        message: "Error running query",
      },
      data: [],
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
