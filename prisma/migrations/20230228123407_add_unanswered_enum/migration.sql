-- AlterEnum
ALTER TYPE "FeedbackState" ADD VALUE 'UNGENERATED';

-- DropForeignKey
ALTER TABLE "Question" DROP CONSTRAINT "Question_dataSourceId_fkey";

-- AlterTable
ALTER TABLE "User" ALTER COLUMN "name" DROP NOT NULL;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_dataSourceId_fkey" FOREIGN KEY ("dataSourceId") REFERENCES "DataSource"("id") ON DELETE CASCADE ON UPDATE CASCADE;
