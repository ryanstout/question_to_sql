-- DropIndex
DROP INDEX "Question_userId_id_questionGroupId_key";

-- CreateIndex
CREATE INDEX "Question_userId_id_questionGroupId_idx" ON "Question"("userId", "id", "questionGroupId");
