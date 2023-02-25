import { Prisma } from "@prisma/client"

import { prisma } from "~/db.server"

import * as evaluationQuestion from "./evaluation-question.server"
import {
  MOCKED_DATASOURCE_RESULTS,
  mockPythonServer,
} from "../../test/python-mocks"

// TODO this is terrible, we should try to use transactions instead :/
//      https://www.simplethread.com/isolated-integration-testing-with-remix-vitest-and-prisma/
async function truncateDB() {
  const tableNames = [Prisma.ModelName.EvaluationQuestionGroup]

  for (const tableName of tableNames) {
    // if (tableName === "_prisma_migrations") {
    //   continue
    // }

    try {
      await prisma.$executeRawUnsafe(
        `TRUNCATE TABLE public."${tableName}" CASCADE;`
      )
    } catch (error) {
      console.log({ error })
    }
  }
}

beforeAll(async () => {
  await truncateDB()
})

// TODO this is a bad idea, we should not rely on seed data
const dataSourceId = 1

it("cascades evaluation question group deletion", async () => {
  const questionGroup =
    await evaluationQuestion.createBlankEvaluationQuestionGroup(dataSourceId)

  await evaluationQuestion.createQuestion(
    questionGroup.id,
    "how many people are there?"
  )

  expect(await prisma.evaluationQuestion.count()).toBe(1)
  expect(await prisma.evaluationQuestionGroup.count()).toBe(1)

  await evaluationQuestion.deleteQuestionGroup(questionGroup.id)

  expect(await prisma.evaluationQuestion.count()).toBe(0)
  expect(await prisma.evaluationQuestionGroup.count()).toBe(0)
})

it("does not clear evaluation question group cache when an earlier question is deleted", async () => {})

it("clears evaluation question group cache when the last question is deleted", async () => {
  mockPythonServer()

  const questionGroup =
    await evaluationQuestion.createBlankEvaluationQuestionGroup(dataSourceId)

  await evaluationQuestion.createQuestion(
    questionGroup.id,
    "how many people are there?"
  )

  const lastQuestion = await evaluationQuestion.createQuestion(
    questionGroup.id,
    "how many families are there?"
  )

  expect(await prisma.evaluationQuestion.count()).toBe(2)
  expect(await prisma.evaluationQuestionGroup.count()).toBe(1)

  let reloadedQuestionGroup =
    await evaluationQuestion.loadEvaluationQuestionGroup(questionGroup.id)

  expect(reloadedQuestionGroup.results).toEqual(MOCKED_DATASOURCE_RESULTS)

  // this should delete the question and clear the results cache
  await evaluationQuestion.deleteQuestion(lastQuestion.id, questionGroup.id)

  // TODO reloading objects is a mess... https://github.com/prisma/prisma/issues/12868
  const questionGroupWithoutCache =
    await prisma.evaluationQuestionGroup.findUniqueOrThrow({
      where: { id: questionGroup.id },
    })

  expect(await prisma.evaluationQuestion.count()).toBe(1)
  expect(await prisma.evaluationQuestionGroup.count()).toBe(1)

  expect(questionGroupWithoutCache.results).toBeNull()
  expect(questionGroupWithoutCache.correctSql).toBeNull()
})
