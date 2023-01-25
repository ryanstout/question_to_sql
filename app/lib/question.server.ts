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

function fakeDataSource() {
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

export async function processQuestion(
  userId: number,
  dataSourceId: number,
  question: string
): Promise<QuestionResult> {
  const dataSource = fakeDataSource()
  const sql = await questionToSql(dataSourceId, question)
  // TODO handle invalid query error
  const data = await runQuery(dataSource, sql)

  const questionRecord = await prisma.question.create({
    data: {
      userId: userId,
      dataSourceId: dataSourceId,

      question: question,
      codexSql: sql,
    },
  })

  return {
    question: questionRecord,
    status: "success",
    data: data,
  }
}

function rootDirectory() {
  return path.resolve(__dirname + "/../..")
}

function pythonCommand() {
  return path.resolve(__dirname + "/../../bin/python-wrapper")
}

function escapeShell(cmd) {
  return '"' + cmd.replace(/(["'$`\\])/g, "\\$1") + '"'
}

export async function questionToSql(
  dataSourceId: number,
  naturalQuestion: string
) {
  return new Promise((resolve, reject) => {
    const pythonPath = pythonCommand()
    log.debug("sending question to python", { path: pythonPath })

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
          resolve(results!.join(""))
        }
      }
    )
  })
}
