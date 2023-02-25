import invariant from "tiny-invariant"

import { EvaluationStatus, Prisma } from "@prisma/client"

import { prisma } from "~/db.server"
import f from "~/functional"
import { log } from "~/lib/logging"
import { runQuery } from "~/lib/python.server"
import { questionToSql } from "~/lib/question.server"

const evaluationQuestionsInclude = {
  evaluationQuestions: {
    // ordering is important for knowing when to clear results cache (i.e. when last question is deleted)
    orderBy: {
      // TODO weird, I cannot use a string here! Some weird nested TS issue
      createdAt: Prisma.SortOrder.asc,
    },
  },
}

export async function loadEvaluationQuestionGroup(evaluationGroupId: number) {
  const dataSourceInclude = {
    dataSource: { select: { name: true } },
  }

  let evaluationGroup = await prisma.evaluationQuestionGroup.findUniqueOrThrow({
    where: { id: evaluationGroupId },
    include: {
      ...evaluationQuestionsInclude,
      ...dataSourceInclude,
    },
  })

  const lastQuestion = evaluationGroup.evaluationQuestions.at(-1)

  // if no correctSql exists, generate it
  if (lastQuestion && f.isBlank(evaluationGroup.correctSql)) {
    log.info("generating sql for evaluation question group")

    const generatedSql =
      lastQuestion.codexSql ??
      (await questionToSql(evaluationGroup.dataSourceId, lastQuestion.question))

    // cache generated SQL on the question
    if (!lastQuestion.codexSql) {
      await prisma.evaluationQuestion.update({
        where: { id: lastQuestion.id },
        data: { codexSql: generatedSql },
      })
    }

    evaluationGroup = await prisma.evaluationQuestionGroup.update({
      where: { id: evaluationGroupId },
      data: { correctSql: generatedSql },
      // TODO this is inefficient to include these objects on each update
      //      but it avoids having to manage model state right now
      include: {
        ...evaluationQuestionsInclude,
        ...dataSourceInclude,
      },
    })
  }

  if (evaluationGroup.correctSql && f.isEmpty(evaluationGroup.results)) {
    log.info("result cache empty, pulling results from data source")

    const results = await runQuery(
      // TODO this is inefficient to include these objects on each update
      //      but it avoids having to manage model state right now
      evaluationGroup.dataSourceId,
      evaluationGroup.correctSql,
      // allow cached queries on training system, but not user side (yet)
      true
    )

    evaluationGroup = await prisma.evaluationQuestionGroup.update({
      where: { id: evaluationGroupId },
      data: { results },
      // TODO this is inefficient to include these objects on each update
      //      but it avoids having to manage model state right now
      include: {
        ...evaluationQuestionsInclude,
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

export async function createEvaluationQuestionGroup(
  questionIdList: number[]
): Promise<void> {
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

  await clearEvaluationQuestionGroupCache(evaluationGroup.id)

  return question
}

// clear the cached results and sql on the evaluation group
// there shouldn't be a case where you would want to clear one, and not the other
async function clearEvaluationQuestionGroupCache(
  evaluationGroupId: number
): Promise<void> {
  await prisma.evaluationQuestionGroup.update({
    where: { id: evaluationGroupId },
    // TODO cannot use null https://github.com/prisma/prisma/issues/13969
    data: { results: Prisma.DbNull, correctSql: null },
  })
}

export async function updateNotes(
  evaluationQuestionGroupId: number,
  notes: string
) {
  await prisma.evaluationQuestionGroup.update({
    where: { id: evaluationQuestionGroupId },
    data: { notes },
  })
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
  evaluationQuestionId: number,
  // we could pull this from the question record, but it's easier to just pass it in
  evaluationQuestionGroupId: number
): Promise<void> {
  log.debug("deleteQuestion", { evaluationQuestionId })

  const evaluationQuestionGroup =
    await prisma.evaluationQuestionGroup.findUniqueOrThrow({
      where: { id: evaluationQuestionGroupId },
      include: {
        ...evaluationQuestionsInclude,
      },
    })

  const lastQuestion = evaluationQuestionGroup.evaluationQuestions.at(-1)
  invariant(
    lastQuestion,
    "last question should exist if we are deleting a question"
  )

  const isDeletingLastQuestion = lastQuestion.id === evaluationQuestionId
  const isCorrectSqlMachineGenerated =
    isDeletingLastQuestion &&
    evaluationQuestionGroup.correctSql === lastQuestion.codexSql

  if (isCorrectSqlMachineGenerated) {
    log.debug("sql is machine generated, deleting cache")
    await clearEvaluationQuestionGroupCache(evaluationQuestionGroupId)
  }

  // if the question being deleted is the last question in the group, then we should clear results and generated SQL
  // iff the correctSql is not machine generated

  await prisma.evaluationQuestion.delete({
    where: { id: evaluationQuestionId },
  })
}
