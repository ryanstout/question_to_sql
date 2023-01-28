-- CreateEnum
CREATE TYPE "FeedbackState" AS ENUM ('INVALID', 'UNANSWERED', 'UNKNOWN', 'CORRECT', 'INCORRECT');

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
CREATE TABLE "QuestionGroup" (
    "id" SERIAL NOT NULL,
    "userId" INTEGER NOT NULL,
    "correctSql" TEXT,

    CONSTRAINT "QuestionGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Question" (
    "id" SERIAL NOT NULL,
    "question" TEXT NOT NULL,
    "dataSourceId" INTEGER,
    "userId" INTEGER NOT NULL,
    "questionGroupId" INTEGER NOT NULL,
    "codexSql" TEXT,
    "userSql" TEXT,
    "resultData" JSONB,
    "feedbackState" "FeedbackState" NOT NULL DEFAULT 'UNANSWERED',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Question_pkey" PRIMARY KEY ("id")
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
    "dataSourceId" INTEGER,
    "skip" BOOLEAN NOT NULL,
    "fullyQualifiedName" TEXT NOT NULL,
    "generatedSQLCache" TEXT NOT NULL,
    "embeddingsCache" JSONB NOT NULL,

    CONSTRAINT "DataSourceTableDescription_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DataSourceTableColumn" (
    "id" SERIAL NOT NULL,
    "skip" BOOLEAN NOT NULL,
    "inspectionMetadata" JSONB NOT NULL,
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "kind" TEXT NOT NULL,
    "isNull" BOOLEAN NOT NULL,
    "default" TEXT NOT NULL,
    "distinctRows" INTEGER NOT NULL,
    "rows" INTEGER NOT NULL,
    "extendedProperties" JSONB NOT NULL,
    "embeddingsCache" JSONB NOT NULL,
    "dataSourceTableDescriptionId" INTEGER,

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
CREATE UNIQUE INDEX "Question_id_userId_questionGroupId_key" ON "Question"("id", "userId", "questionGroupId");

-- CreateIndex
CREATE UNIQUE INDEX "DataSourceTableDescription_dataSourceId_fullyQualifiedName_key" ON "DataSourceTableDescription"("dataSourceId", "fullyQualifiedName");

-- AddForeignKey
ALTER TABLE "User" ADD CONSTRAINT "User_businessId_fkey" FOREIGN KEY ("businessId") REFERENCES "Business"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Password" ADD CONSTRAINT "Password_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "QuestionGroup" ADD CONSTRAINT "QuestionGroup_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_dataSourceId_fkey" FOREIGN KEY ("dataSourceId") REFERENCES "DataSource"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Question" ADD CONSTRAINT "Question_questionGroupId_fkey" FOREIGN KEY ("questionGroupId") REFERENCES "QuestionGroup"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DataSource" ADD CONSTRAINT "DataSource_businessId_fkey" FOREIGN KEY ("businessId") REFERENCES "Business"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DataSourceTableDescription" ADD CONSTRAINT "DataSourceTableDescription_dataSourceId_fkey" FOREIGN KEY ("dataSourceId") REFERENCES "DataSource"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DataSourceTableColumn" ADD CONSTRAINT "DataSourceTableColumn_dataSourceTableDescriptionId_fkey" FOREIGN KEY ("dataSourceTableDescriptionId") REFERENCES "DataSourceTableDescription"("id") ON DELETE SET NULL ON UPDATE CASCADE;
