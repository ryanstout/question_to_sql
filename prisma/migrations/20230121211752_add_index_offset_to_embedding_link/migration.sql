/*
  Warnings:

  - Added the required column `indexOffset` to the `EmbeddingLink` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "EmbeddingLink" ADD COLUMN     "indexOffset" INTEGER NOT NULL;

-- CreateIndex
CREATE INDEX "EmbeddingLink_indexNumber_indexOffset_idx" ON "EmbeddingLink"("indexNumber", "indexOffset");
