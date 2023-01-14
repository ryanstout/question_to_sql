/*
  Warnings:

  - A unique constraint covering the columns `[id,userId,questionGroupId]` on the table `Question` will be added. If there are existing duplicate values, this will fail.

*/
-- DropIndex
DROP INDEX "Question_userId_id_questionGroupId_idx";

-- CreateIndex
CREATE UNIQUE INDEX "Question_id_userId_questionGroupId_key" ON "Question"("id", "userId", "questionGroupId");
