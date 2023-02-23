import { prisma } from "~/db.server"

import evaluationQuestion from "./evaluation-question.server"

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
