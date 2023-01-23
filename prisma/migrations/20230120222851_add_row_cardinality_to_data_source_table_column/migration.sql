/*
  Warnings:

  - Added the required column `distinctRows` to the `DataSourceTableColumn` table without a default value. This is not possible if the table is not empty.
  - Added the required column `rows` to the `DataSourceTableColumn` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "DataSourceTableColumn" ADD COLUMN     "distinctRows" INTEGER NOT NULL,
ADD COLUMN     "rows" INTEGER NOT NULL;
