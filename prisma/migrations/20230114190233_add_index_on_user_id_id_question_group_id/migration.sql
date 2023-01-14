/*
  Warnings:

  - A unique constraint covering the columns `[userId,id,questionGroupId]` on the table `Question` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "Question_userId_id_questionGroupId_key" ON "Question"("userId", "id", "questionGroupId");
