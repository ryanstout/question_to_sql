import { EvaluationStatus } from "@prisma/client"

import { prisma } from "~/db.server"
import { log } from "~/lib/logging.server"
import { runQuery } from "~/lib/question.server"

export async function createEvaluationQuestionGroup(questionIdList: number[]) {
  log.info("creating question group", { questionIdList })

  // create a new evaluation group
  const evaluationQuestionGroup = await prisma.evaluationQuestionGroup.create({
    data: {
      dataSourceId: 1,
    },
  })

  // convert each of the questions into an evaluation question
  for (const questionId of questionIdList) {
    await createEvaluationQuestionFromQuestion(
      questionId,
      evaluationQuestionGroup.id
    )
  }
}

export async function createEvaluationQuestionFromQuestion(
  questionId: number,
  evaluationQuestionGroupId: number
) {
  const questionRecord = await prisma.question.findUniqueOrThrow({
    where: { id: questionId },
  })

  const evaluationQuestion = await prisma.evaluationQuestion.create({
    data: {
      evaluationQuestionGroupId,

      fromQuestionId: questionRecord.id,
      question: questionRecord.question,

      // TODO should we include the results here?
    },
  })

  return evaluationQuestion
}

export async function updateQuestion(
  evaluationQuestionGroupId: number,
  sql: string
): Promise<void> {
  const evaluationQuestionGroup =
    await prisma.evaluationQuestionGroup.findUniqueOrThrow({
      where: { id: evaluationQuestionGroupId },
    })

  // TODO should probably use a purpose-built method here so we can have python update the generatedSchema & prompt
  const results = await runQuery(evaluationQuestionGroup.dataSourceId, sql)

  // update result & correctSql on evaluation group
  await prisma.evaluationQuestionGroup.update({
    where: { id: evaluationQuestionGroup.id },
    data: { correctSql: sql, results: results },
  })

  // TODO need to update the generatedSchema & generatedPrompt on the backend
}

export async function createQuestion(
  evaluationGroupId: number,
  questionText: string
) {
  const evaluationGroup =
    await prisma.evaluationQuestionGroup.findUniqueOrThrow({
      where: { id: evaluationGroupId },
    })

  const question = await prisma.evaluationQuestion.create({
    data: {
      question: questionText,
      evaluationQuestionGroupId: evaluationGroup.id,
    },
  })

  // clear the cached data on the evaluation group
  await prisma.evaluationQuestionGroup.update({
    where: { id: evaluationGroup.id },
    data: { results: [], correctSql: null },
  })

  return question
}

export async function markCorrect(
  evaluationQuestionGroupId: number,
  notes?: string
): Promise<void> {
  await prisma.evaluationQuestionGroup.update({
    where: { id: evaluationQuestionGroupId },
    data: { notes, status: EvaluationStatus.CORRECT },
  })
}

export default { updateQuestion, createQuestion, markCorrect }
