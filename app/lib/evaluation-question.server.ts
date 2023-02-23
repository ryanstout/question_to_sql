import { EvaluationStatus } from "@prisma/client"

import { prisma } from "~/db.server"
import f from "~/functional"
import { log } from "~/lib/logging"
import { runQuery } from "~/lib/python.server"
import { questionToSql } from "~/lib/question.server"

export async function loadEvaluationQuestionGroup(evaluationGroupId: number) {
  const dataSourceInclude = { dataSource: { select: { name: true } } }

  let evaluationGroup = await prisma.evaluationQuestionGroup.findUniqueOrThrow({
    where: { id: evaluationGroupId },
    include: {
      evaluationQuestions: true,
      ...dataSourceInclude,
    },
  })

  const lastQuestion = evaluationGroup.evaluationQuestions.at(-1)

  // if no correctSql exists, generate it
  if (lastQuestion && f.isBlank(evaluationGroup.correctSql)) {
    log.info("generating sql for evaluation question group")

    const generatedSql = await questionToSql(
      evaluationGroup.dataSourceId,
      lastQuestion.question
    )

    evaluationGroup = await prisma.evaluationQuestionGroup.update({
      where: { id: evaluationGroupId },
      data: { correctSql: generatedSql },
      // TODO this is inefficient, but it avoids having to manage model state right now
      include: {
        evaluationQuestions: true,
        ...dataSourceInclude,
      },
    })
  }

  if (evaluationGroup.correctSql && f.isEmpty(evaluationGroup.results)) {
    log.info("result cache empty, generating")

    const results = await runQuery(
      evaluationGroup.dataSourceId,
      evaluationGroup.correctSql,
      // allow cached queries on training system, but not user side (yet)
      true
    )

    evaluationGroup = await prisma.evaluationQuestionGroup.update({
      where: { id: evaluationGroupId },
      data: { results },
      // TODO this is inefficient, but it avoids having to manage model state right now
      include: {
        evaluationQuestions: true,
        ...dataSourceInclude,
      },
    })
  }

  return evaluationGroup
}

export async function createBlankEvaluationQuestionGroup(dataSourceId: number) {
  const questionGroup = await prisma.evaluationQuestionGroup.create({
    data: {
      status: EvaluationStatus.UNREAD,
      dataSourceId: dataSourceId,
    },
  })

  // TODO is this not thrown automatically if there's a schema failure?
  if (!questionGroup) {
    throw new Error("Failed to create question group")
  }

  return questionGroup
}

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
  const results = await runQuery(
    evaluationQuestionGroup.dataSourceId,
    sql,
    // allow caching on training system, but not user side (yet)
    true
  )

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
  notes?: string,
  assertionColumns?: string[]
): Promise<void> {
  await prisma.evaluationQuestionGroup.update({
    where: { id: evaluationQuestionGroupId },
    data: { notes, status: EvaluationStatus.CORRECT, assertionColumns },
  })
}

export async function deleteQuestionGroup(
  evaluationQuestionGroupId: number
): Promise<void> {
  log.debug("deleteQuestionGroup", { evaluationQuestionGroupId })

  await prisma.evaluationQuestionGroup.delete({
    where: { id: evaluationQuestionGroupId },
  })
}

export async function deleteQuestion(
  evaluationQuestionId: number
): Promise<void> {
  log.debug("deleteQuestion", { evaluationQuestionId })

  await prisma.evaluationQuestion.delete({
    where: { id: evaluationQuestionId },
  })
}

// TODO is there a way to just auto-export all exports in the file?
// TODO maybe this is an anti-pattern? I don't like importing a ton of methods without context of where they are from
export default {
  updateQuestion,
  createQuestion,
  markCorrect,
  deleteQuestionGroup,
  deleteQuestion,
  createBlankEvaluationQuestionGroup,
}
