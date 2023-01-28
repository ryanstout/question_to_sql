import type { Question } from "@prisma/client"

import { prisma } from "~/db.server"
import { log } from "~/lib/logging.server"
import { runQuery } from "~/lib/query-runner"

interface QuestionResult {
  question: Question
  status: "success" | "error"
  data?: any[]
}

// TODO we should rip this out!
export function fakeDataSource() {
  return {
    // TODO this is a total hack for not having a proper user
    type: "snowflake",
    id: 1,
    credentials: {
      account: process.env.SNOWFLAKE_ACCOUNT,
      username: process.env.SNOWFLAKE_USERNAME,
      password: process.env.SNOWFLAKE_PASSWORD,
      database: process.env.SNOWFLAKE_DATABASE,
      schema: process.env.SNOWFLAKE_SCHEMA,
      warehouse: process.env.SNOWFLAKE_WAREHOUSE,
    },
  }
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
      include: {
        questionGroup: {
          include: {
            questions: true,
          },
        },
      },
    })
  }

  if (retrievedQuestionRecord === null) {
    throw new Error("question record not found")
  }

  const dataSource = fakeDataSource()
  const data = await runQuery(dataSource, retrievedQuestionRecord.codexSql)

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

  const dataSource = fakeDataSource()
  log.debug("sending updated query to snowflake")
  const results = await runQuery(dataSource, userSql)

  return {
    question: updateUser,
    status: "success",
    data: results,
  }
}

export async function processQuestion(
  userId: number,
  dataSourceId: number,
  question: string,
  questionGroupId?: number
): Promise<QuestionResult> {
  const dataSource = fakeDataSource()

  if (!questionGroupId) {
    const questionGroup = await prisma.questionGroup.create({
      data: {
        userId: userId,
      },
    })

    questionGroupId = questionGroup.id
  }

  // create the question first, in case open AI fails
  let questionRecord = await prisma.question.create({
    data: {
      userId: userId,
      dataSourceId: dataSourceId,
      questionGroupId: questionGroupId,
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
      codexSql: sql,
    },
  })

  // TODO catch and mark as invalid if this fails
  const data = await runQuery(dataSource, sql)
  log.debug("got data from snowflake")

  return {
    question: questionRecord,
    status: "success",
    data: data,
  }
}

export async function questionToSql(
  dataSourceId: number,
  naturalQuestion: string
): Promise<string> {
  // TODO remove me! Use mock server once we have a python API
  if (process.env.MOCKED_QUESTION_RESPONSE === "true") {
    return new Promise((resolve, reject) => {
      resolve("SELECT * FROM ORDERS LIMIT 10")
    })
  }

  const serverHost = process.env.PYTHON_SERVER
  const postURL = `${serverHost}/question`

  log.debug("converting question to sql", { postURL, naturalQuestion })

  const response = await fetch(postURL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      data_source_id: dataSourceId,
      question: naturalQuestion,
    }),
  })

  const json = await response.json()
  return json["sql"]
}
