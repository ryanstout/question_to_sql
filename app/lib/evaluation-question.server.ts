import invariant from "tiny-invariant"

import { prisma } from "~/db.server"
import { log } from "~/lib/logging.server"

export async function createEvaluationQuestionGroup(questionIdList: number[]) {
  log.info("creating question group", { questionIdList })

  // create a new evaluation group
  const evaluationQuestionGroup = await prisma.evaluationQuestionGroup.create({
    data: {
      dataSourceId: 1,
    },
  })

  invariant(evaluationQuestionGroup, "evaluation question group not created")

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
  const questionRecord = await prisma.question.findUnique({
    where: { id: questionId },
  })

  invariant(questionRecord, "question not found")

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
