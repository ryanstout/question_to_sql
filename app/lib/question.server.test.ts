import * as pythonBackend from "~/lib/python.server"
import {
  createQuestion,
  getResultsFromQuestion,
  updateQuestion,
} from "~/lib/question.server"

const dataSourceId = 1
const userId = 1

// TODO the below mocking stuff needs to be extracted out as soon as it is needed elsewhere

// TODO this has got to be in some stdlib somewhere, right?
function promisifyStaticValue<T>(value: T): Promise<T> {
  return new Promise((resolve, reject) => {
    resolve(value)
  })
}

const MOCKED_RESULTS = [{ count: 100 }]
const MOCKED_SQL_RESULT = "SELECT * FROM ORDER LIMIT 10"

function mockPythonServer() {
  const runQuerySpy = vi
    .spyOn(pythonBackend, "runQuery")
    .mockReturnValue(promisifyStaticValue(MOCKED_RESULTS))

  const pythonRequestSpy = vi
    .spyOn(pythonBackend, "pythonRequest")
    .mockReturnValue(promisifyStaticValue({ sql: MOCKED_SQL_RESULT }))

  return { runQuerySpy, pythonRequestSpy }

  // TODO I'm not convinced the above is the right way to do this, an alternative is below
  //      but has some pretty significant downsides
  // vi.mock("~/lib/python.server", async (importOriginal) => {
  //   const MOCKED_SQL_RESULT = "SELECT * FROM ORDER LIMIT 10"
  //   const mod = await importOriginal()

  //   return {
  //     ...mod,
  //     // questionToSql: vi
  //     //   .fn()
  //     //   .mockReturnValue(promisifyStaticValue(MOCKED_SQL_RESULT)),
  //     pythonRequest: () =>
  //       promisifyStaticValue({ sql: "SELECT * FROM ORDER LIMIT 10" }),
  //     // questionToSql: () => console.log("did we do it?"),
  //     runQuery: vi
  //       .fn()
  //       .mockReturnValue(promisifyStaticValue(MOCKED_SQL_RESULT)),
  //   }
  // })
}

const { runQuerySpy } = mockPythonServer()

// TODO need to use test DB
// TODO need to mock data source
test("processes a new question", async () => {
  const questionResult = await createQuestion(
    userId,
    dataSourceId,
    "What is the total number of orders?"
  )

  expect(questionResult.status).toBe("success")
  expect(questionResult.data).toBeNull()
  expect(questionResult.question.userSql).toBeNull()
  // TODO should create fixture for this
  expect(questionResult.question.sql).toBe("SELECT * FROM ORDER LIMIT 10")
})

test("updates a question sql", async () => {
  const questionResult = await createQuestion(
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

test("gets results from a question with custom user sql", async () => {
  const questionResult = await createQuestion(
    userId,
    dataSourceId,
    "What is the total number of orders?"
  )

  const updatedSql = "SELECT * FROM PLACES LIMIT 10"
  const updatedQuestion = await updateQuestion(
    questionResult.question,
    updatedSql
  )

  const results = await getResultsFromQuestion({
    questionRecord: updatedQuestion.question,
  })

  expect(results.status).toBe("success")
  expect(results.data).toEqual(MOCKED_RESULTS)

  const lastQueryCall = runQuerySpy.mock.calls.at(-1)!
  expect(lastQueryCall[1]).toEqual(updatedSql)
})

test("gets results from a question", async () => {
  const questionResult = await createQuestion(
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
  const questionResult = await createQuestion(
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
