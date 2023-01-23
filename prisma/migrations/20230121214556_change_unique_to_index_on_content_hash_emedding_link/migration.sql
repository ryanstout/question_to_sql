-- DropIndex
DROP INDEX "EmbeddingLink_contentHash_tableId_columnId_key";

-- CreateIndex
CREATE INDEX "EmbeddingLink_contentHash_tableId_columnId_idx" ON "EmbeddingLink"("contentHash", "tableId", "columnId");
