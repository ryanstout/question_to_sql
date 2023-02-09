import {
  getResultsFromQuestion,
  processQuestion,
  updateQuestion,
} from "~/lib/question.server"

const MOCKED_RESULTS = [{ count: 100 }]

// TODO need to use test DB
// TODO need to mock data source
test("processes a new question", async () => {
  const dataSourceId = 1
  const userId = 1
  const questionResult = await processQuestion(
    userId,
    dataSourceId,
    "What is the total number of orders?"
  )

  expect(questionResult.status).toBe("success")
  // TODO should create fixture for this
  expect(questionResult.data).toEqual(MOCKED_RESULTS)
  expect(questionResult.question.userSql).toBeNull()
  // TODO should create fixture for this
  expect(questionResult.question.codexSql).toBe("SELECT * FROM ORDER LIMIT 10")
})

test("updates a question", async () => {
  const dataSourceId = 1
  const userId = 1
  const questionResult = await processQuestion(
    userId,
    dataSourceId,
    "What is the total number of orders?"
  )

  const updatedSql = "SELECT * FROM customers LIMIT 10"
  const updatedQuestion = await updateQuestion(
    questionResult.question,
    updatedSql
  )

  expect(updatedQuestion.question.userSql).toBe(updatedSql)
})

test("gets results from a question", async () => {
  const dataSourceId = 1
  const userId = 1
  const questionResult = await processQuestion(
    userId,
    dataSourceId,
    "What is the total number of orders?"
  )

  const results = await getResultsFromQuestion({
    questionRecord: questionResult.question,
  })

  expect(results.status).toBe("success")
  expect(results.data).toEqual(MOCKED_RESULTS)
})

test("gets results from question ID", async () => {
  const dataSourceId = 1
  const userId = 1
  const questionResult = await processQuestion(
    userId,
    dataSourceId,
    "What is the total number of orders?"
  )

  const results = await getResultsFromQuestion({
    questionId: questionResult.question.id,
  })

  expect(results.status).toBe("success")
  expect(results.data).toEqual(MOCKED_RESULTS)
})
