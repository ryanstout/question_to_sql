-- CreateEnum
CREATE TYPE "FeedbackState" AS ENUM ('INVALID', 'UNANSWERED', 'UNKNOWN', 'CORRECT', 'INCORRECT');

-- CreateEnum
CREATE TYPE "EvaluationOperators" AS ENUM ('EQUALS', 'CONTAINS');

-- CreateEnum
CREATE TYPE "EvaluationStatus" AS ENUM ('UNREAD', 'INCOMPLETE', 'CORRECT');

-- CreateEnum
CREATE TYPE "DataSourceType" AS ENUM ('SNOWFLAKE', 'POSTGRES');

-- CreateTable
CREATE TABLE "User" (
    "id" SERIAL NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "businessId" INTEGER,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Password" (
    "hash" TEXT NOT NULL,
    "userId" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "Question" (
    "id" SERIAL NOT NULL,
    "question" TEXT NOT NULL,
    "dataSourceId" INTEGER NOT NULL,
    "userId" INTEGER NOT NULL,
    "sql" TEXT,
    "userSql" TEXT,
    "feedbackState" "FeedbackState" NOT NULL DEFAULT 'UNANSWERED',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Question_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EvaluationQuestionGroup" (
    "id" SERIAL NOT NULL,
    "status" "EvaluationStatus" NOT NULL DEFAULT 'UNREAD',
    "dataSourceId" INTEGER NOT NULL,
    "correctSql" TEXT,
    "result" JSONB,
    "resultOperator" "EvaluationOperators" NOT NULL DEFAULT 'EQUALS',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "EvaluationQuestionGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EvaluationQuestion" (
    "id" SERIAL NOT NULL,
    "evaluationQuestionGroupId" INTEGER NOT NULL,
    "fromQuestionId" INTEGER,
    "generatedSchema" TEXT,
    "generatedPrompt" TEXT,
    "question" TEXT NOT NULL,
    "codexSql" TEXT,
    "notes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "EvaluationQuestion_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EvaluationResult" (
    "id" SERIAL NOT NULL,
    "successfulQuestions" JSONB NOT NULL,
    "failedQuestions" JSONB NOT NULL,
    "evaluatedAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "EvaluationResult_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Business" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Business_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DataSource" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "credentials" JSONB NOT NULL,
    "type" "DataSourceType" NOT NULL,
    "businessId" INTEGER,

    CONSTRAINT "DataSource_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DataSourceTableDescription" (
    "id" SERIAL NOT NULL,
    "dataSourceId" INTEGER NOT NULL,
    "skip" BOOLEAN NOT NULL DEFAULT false,
    "fullyQualifiedName" TEXT NOT NULL,
    "generatedSQLCache" TEXT,
    "embeddingsCache" JSONB DEFAULT '{}',

    CONSTRAINT "DataSourceTableDescription_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DataSourceTableColumn" (
    "id" SERIAL NOT NULL,
    "dataSourceId" INTEGER NOT NULL,
    "skip" BOOLEAN NOT NULL DEFAULT false,
    "inspectionMetadata" JSONB NOT NULL DEFAULT '{}',
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "kind" TEXT NOT NULL,
    "isNull" BOOLEAN NOT NULL,
    "default" TEXT,
    "distinctRows" INTEGER NOT NULL,
    "rows" INTEGER NOT NULL,
    "extendedProperties" JSONB NOT NULL,
    "embeddingsCache" JSONB NOT NULL DEFAULT '{}',
    "dataSourceTableDescriptionId" INTEGER NOT NULL,

    CONSTRAINT "DataSourceTableColumn_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EmbeddingCache" (
    "id" SERIAL NOT NULL,
    "contentHash" TEXT NOT NULL,
    "embedding" BYTEA NOT NULL,

    CONSTRAINT "EmbeddingCache_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "Password_userId_key" ON "Password"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "Question_id_userId_key" ON "Question"("id", "userId");

-- CreateIndex
CREATE UNIQUE INDEX "DataSourceTableDescription_dataSourceId_fullyQualifiedName_key" ON "DataSourceTableDescription"("dataSourceId", "fullyQualifiedName");

-- AddForeignKey
ALTER TABLE "User" ADD CONSTRAINT "User_businessId_fkey" FOREIGN KEY ("businessId") REFERENCES "Business"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Password" ADD CONSTRAINT "Password_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_dataSourceId_fkey" FOREIGN KEY ("dataSourceId") REFERENCES "DataSource"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EvaluationQuestionGroup" ADD CONSTRAINT "EvaluationQuestionGroup_dataSourceId_fkey" FOREIGN KEY ("dataSourceId") REFERENCES "DataSource"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EvaluationQuestion" ADD CONSTRAINT "EvaluationQuestion_evaluationQuestionGroupId_fkey" FOREIGN KEY ("evaluationQuestionGroupId") REFERENCES "EvaluationQuestionGroup"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EvaluationQuestion" ADD CONSTRAINT "EvaluationQuestion_fromQuestionId_fkey" FOREIGN KEY ("fromQuestionId") REFERENCES "Question"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DataSource" ADD CONSTRAINT "DataSource_businessId_fkey" FOREIGN KEY ("businessId") REFERENCES "Business"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DataSourceTableDescription" ADD CONSTRAINT "DataSourceTableDescription_dataSourceId_fkey" FOREIGN KEY ("dataSourceId") REFERENCES "DataSource"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DataSourceTableColumn" ADD CONSTRAINT "DataSourceTableColumn_dataSourceId_fkey" FOREIGN KEY ("dataSourceId") REFERENCES "DataSource"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DataSourceTableColumn" ADD CONSTRAINT "DataSourceTableColumn_dataSourceTableDescriptionId_fkey" FOREIGN KEY ("dataSourceTableDescriptionId") REFERENCES "DataSourceTableDescription"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
