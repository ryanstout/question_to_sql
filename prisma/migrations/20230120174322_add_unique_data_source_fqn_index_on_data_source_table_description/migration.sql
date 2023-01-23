/*
  Warnings:

  - A unique constraint covering the columns `[dataSourceId,fullyQualifiedName]` on the table `DataSourceTableDescription` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "DataSourceTableDescription_dataSourceId_fullyQualifiedName_key" ON "DataSourceTableDescription"("dataSourceId", "fullyQualifiedName");
