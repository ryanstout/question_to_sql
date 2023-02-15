import type { Question } from "@prisma/client"

import { prisma } from "~/db.server"

export interface HistoryResult {
  questionHistory: Question[]
  status: "success" | "error"
}

export async function getUserQuestionHistory(
  userId: number,
  dataSourceId: number
): Promise<HistoryResult> {
  // TODO implement pagination in fetch - perhaps https://www.prisma.io/docs/concepts/components/prisma-client/pagination

  const questionHistory = await prisma.question.findMany({
    where: {
      userId: userId,
      dataSourceId: dataSourceId,
    },
    include: {
      user: true,
    },
    orderBy: { createdAt: "desc" },
  })

  return {
    questionHistory: questionHistory,
    status: "success",
  }
}
