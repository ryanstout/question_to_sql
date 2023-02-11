import invariant from "tiny-invariant"

import type { Question } from "@prisma/client"

import { prisma } from "~/db.server"
import { log } from "~/lib/logging.server"

export interface QuestionResult {
  question: Question
  status: "success" | "error"
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

  invariant(retrievedQuestionRecord !== null, "question record not found")
  invariant(retrievedQuestionRecord.sql !== null, "sql is null")

  const data = await runQuery(
    retrievedQuestionRecord.dataSourceId,
    retrievedQuestionRecord.sql
  )

  return {
    question: retrievedQuestionRecord,
    status: "success",
    data: data,
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

// runs SQL and gets a result
async function runQuery(dataSourceId: number, sql: string) {
  if (process.env.MOCKED_QUESTION_RESPONSE === "true") {
    return new Promise((resolve, reject) => {
      resolve([{ count: 100 }])
    })
  }

  const response = await pythonRequest("query", {
    data_source_id: dataSourceId,
    sql: sql,
  })

  return response["results"]
}

async function questionToSql(
  dataSourceId: number,
  naturalQuestion: string
): Promise<string> {
  // TODO remove me! Use mock server once we have a python API
  if (process.env.MOCKED_QUESTION_RESPONSE === "true") {
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

// TODO we need an openapi spec for the python server so we have full stack typing
async function pythonRequest(endpoint: string, requestParams: any) {
  const serverHost = process.env.PYTHON_SERVER
  invariant(serverHost, "PYTHON_SERVER env var not set")

  const postURL = `${serverHost}/${endpoint}`

  log.debug("making python request", {
    requestParams,
    postURL,
  })

  const response = await fetch(postURL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestParams),
  })

  const json = await response.json()
  return json
}
