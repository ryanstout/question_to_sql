import type { Question } from "@prisma/client"
import path from "path"
import { PythonShell } from "python-shell"

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
export async function getResultsFromQuestion(
  question: Question
): Promise<QuestionResult> {
  const dataSource = fakeDataSource()
  const data = await runQuery(dataSource, question.codexSql)

  return {
    question: question,
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

function rootDirectory() {
  return path.resolve(__filename + "/../..")
}

function pythonCommand() {
  return path.resolve(__filename + "/../../bin/python-wrapper")
}

function escapeShell(cmd: string) {
  return '"' + cmd.replace(/(["'$`\\])/g, "\\$1") + '"'
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

  return new Promise((resolve, reject) => {
    const pythonPath = pythonCommand()
    log.debug("sending question to python", {
      question: naturalQuestion,
      path: pythonPath,
    })

    PythonShell.run(
      "python/answer.py",
      {
        pythonPath: pythonPath,
        mode: "text",
        cwd: rootDirectory(),
        args: [
          "--data-source-id",
          dataSourceId.toString(),
          "--question",
          escapeShell(naturalQuestion),
        ],
      },
      (err, results) => {
        if (err) {
          log.error("error running python", { results })
          reject(err)
        } else {
          resolve(results!.join("\n"))
        }
      }
    )
  })
}
