import type { Question } from "@prisma/client"
import { PythonShell } from "python-shell"

import { prisma } from "~/db.server"
import { runQuery } from "~/lib/query-runner"

interface QuestionResult {
  question: Question
  status: "success" | "error"
  data: any[]
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
): QuestionResult {
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

export async function questionToSql(
  dataSourceId: number,
  naturalQuestion: string
) {
  return new Promise((resolve, reject) => {
    PythonShell.run(
      "python/answer.py",
      {
        pythonPath:
          "/Users/mike/Library/Caches/pypoetry/virtualenvs/nlpquery-bkN6bad3-py3.9/bin/python",
        mode: "text",
        args: ["--data-source-id", dataSourceId, "--question", naturalQuestion],
      },
      (err, results) => {
        if (err) {
          reject(err)
        } else {
          resolve(results)
        }
      }
    )
  })
}
