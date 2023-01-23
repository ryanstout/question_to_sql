/*
  Warnings:

  - You are about to drop the column `correctState` on the `Question` table. All the data in the column will be lost.
  - Added the required column `feedbackState` to the `Question` table without a default value. This is not possible if the table is not empty.

*/
-- CreateEnum
CREATE TYPE "FeedbackState" AS ENUM ('UNKNOWN', 'CORRECT', 'INCORRECT');

-- DropIndex
DROP INDEX "EmbeddingLink_indexNumber_indexOffset_idx";

-- AlterTable
ALTER TABLE "EmbeddingLink" ADD COLUMN     "dataSourceId" INTEGER;

-- AlterTable
ALTER TABLE "Question" DROP COLUMN "correctState",
ADD COLUMN     "feedbackState" "FeedbackState" NOT NULL,
ADD COLUMN     "resultData" JSONB;

-- CreateIndex
CREATE INDEX "EmbeddingLink_dataSourceId_indexNumber_indexOffset_idx" ON "EmbeddingLink"("dataSourceId", "indexNumber", "indexOffset");

-- AddForeignKey
ALTER TABLE "EmbeddingLink" ADD CONSTRAINT "EmbeddingLink_dataSourceId_fkey" FOREIGN KEY ("dataSourceId") REFERENCES "DataSource"("id") ON DELETE SET NULL ON UPDATE CASCADE;
