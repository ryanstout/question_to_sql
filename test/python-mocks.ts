import * as pythonBackend from "~/lib/python.server"

// TODO the below mocking stuff needs to be extracted out as soon as it is needed elsewhere

export const MOCKED_DATASOURCE_RESULTS = [{ count: 100 }]
export const MOCKED_SQL_RESULT = "SELECT * FROM ORDER LIMIT 10"

export function mockPythonServer() {
  const runQuerySpy = vi
    .spyOn(pythonBackend, "runQuery")
    .mockReturnValue(Promise.resolve(MOCKED_DATASOURCE_RESULTS))

  const pythonRequestSpy = vi
    .spyOn(pythonBackend, "pythonRequest")
    .mockReturnValue(Promise.resolve({ sql: MOCKED_SQL_RESULT }))

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
