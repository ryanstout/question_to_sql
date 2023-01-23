-- CreateTable
CREATE TABLE "EmbeddingLink" (
    "id" SERIAL NOT NULL,
    "indexNumber" INTEGER NOT NULL,
    "contentHash" TEXT NOT NULL,
    "tableId" INTEGER,
    "columnId" INTEGER,

    CONSTRAINT "EmbeddingLink_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EmbeddingCache" (
    "id" SERIAL NOT NULL,
    "contentHash" TEXT NOT NULL,
    "embedding" BYTEA NOT NULL,

    CONSTRAINT "EmbeddingCache_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "EmbeddingLink_contentHash_tableId_columnId_key" ON "EmbeddingLink"("contentHash", "tableId", "columnId");

-- AddForeignKey
ALTER TABLE "EmbeddingLink" ADD CONSTRAINT "EmbeddingLink_tableId_fkey" FOREIGN KEY ("tableId") REFERENCES "DataSourceTableDescription"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EmbeddingLink" ADD CONSTRAINT "EmbeddingLink_columnId_fkey" FOREIGN KEY ("columnId") REFERENCES "DataSourceTableColumn"("id") ON DELETE SET NULL ON UPDATE CASCADE;
