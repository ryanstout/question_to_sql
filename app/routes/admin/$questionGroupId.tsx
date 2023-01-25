import { sql } from "@codemirror/lang-sql"
import { EditorView } from "@codemirror/view"
import type { Question } from "@prisma/client"
import { FeedbackState } from "@prisma/client"
import CodeMirror from "@uiw/react-codemirror"
import beautify from "json-beautify"
import { useEffect, useState } from "react"
import { z } from "zod"
import { zx } from "zodix"

import type { ActionArgs, LoaderFunction } from "@remix-run/node"
import { redirect } from "@remix-run/node"
import {
  Form,
  Outlet,
  useCatch,
  useLoaderData,
  useNavigation,
  useParams,
  useSearchParams,
  useSubmit,
} from "@remix-run/react"

import {
  AppShell,
  Box,
  Button,
  Flex,
  Grid,
  Header,
  Loader,
  Stack,
  Table,
  Text,
  TextInput,
} from "@mantine/core"

import { Footer } from "~/components/admin/footer"
import { prisma } from "~/db.server"
import { log } from "~/lib/logging.server"
import { runQuery } from "~/lib/query-runner"
import { fakeDataSource, questionToSql } from "~/lib/question.server"
import { requireUserId } from "~/session.server"

type QuestionInBrowser = Pick<
  Question,
  "id" | "question" | "questionGroupId" | "userSql" | "feedbackState"
>

type LoaderData = {
  questions: QuestionInBrowser[]
  questionGroupId: number
  latestResult: string
} | null

export async function findOrCreateQuestionGroup(
  userId: number,
  questionGroupId: number | null
) {
  // TODO I think we can use `prisma.user.upsert` here instead

  // See if the questionGroup already exists
  let questionGroup = questionGroupId
    ? await prisma.questionGroup.findFirst({
        where: { id: questionGroupId, userId: userId },
      })
    : null

  if (!questionGroup) {
    // create a question group if it doesn't exist
    questionGroup = await prisma.questionGroup.create({
      data: {
        userId: userId,
      },
    })
  }

  return questionGroup
}

// Not, questionGroupId should already be vetted
async function findOrCreateQuestion(
  userId: number,
  q: string,
  questionGroupId: number
) {
  // check to see if the question already exists
  let question = await prisma.question.findFirst({
    where: { questionGroupId: questionGroupId, question: q, userId: userId },
  })

  if (!question) {
    // TODO route to new generator
    // create the question if it doesn't exist

    const dataSource = fakeDataSource()

    // We need to generate the sql for the query since its new
    const codexSql = await questionToSql(dataSource.id, q)

    // create the new query
    question = await prisma.question.create({
      data: {
        questionGroupId: questionGroupId,
        question: q,
        userId: userId,
        userSql: codexSql,
        codexSql: codexSql,
        feedbackState: FeedbackState.UNANSWERED,
      },
    })
  }

  // Load all questions and return them
  const questions = await prisma.question.findMany({
    select: {
      id: true,
      question: true,
      questionGroupId: true,
      userSql: true,
      feedbackState: true,
    },
    where: { questionGroupId: questionGroupId, userId: userId },
  })

  return questions
}

export async function action({ request }: ActionArgs) {
  const userId = await requireUserId(request)

  // create the query, attempt to load the generated sql if it doesn't exist,
  // then redirect to the query page
  // NOTE: q may get put in the url also, but needs to come from the form first
  let { q, action_name, questionGroupId } = await zx.parseForm(request, {
    q: z.string().optional(),
    action_name: z.string().optional(),
    questionGroupId: zx.NumAsString,
  })

  const q2 = zx.parseQuery(request, { q: z.string().optional() })
  if (q2) {
    q ||= q2.q
  }

  // make sure questionGroup exists
  let questionGroup = await findOrCreateQuestionGroup(userId, questionGroupId)

  let questions: QuestionInBrowser[] | null
  let question

  // updating the usersql, not the original question
  if (action_name === "update") {
    const { id, userSql } = await zx.parseForm(request, {
      id: zx.NumAsString,
      userSql: z.string(),
    })

    // TODO: figure out why multiple fields in where clauses on update
    // doesn't work, for now checking the question exists for the user
    // first
    question = prisma.question.findFirst({
      where: {
        id: id,
        userId: userId,
        questionGroupId: questionGroup.id,
      },
    })

    if (!question) {
      throw new Error("Unable to find question to update")
    }

    await prisma.question.update({
      data: {
        userSql: userSql as string,
      },
      where: {
        id: id,
      },
    })
  } else if (
    action_name === "mark_correct" ||
    action_name === "mark_incorrect"
  ) {
    const { q } = await zx.parseQuery(request, { q: z.string() })
    const question = await prisma.question.findFirst({
      select: { id: true },
      where: {
        questionGroupId: questionGroup.id,
        userId: userId,
        question: q,
      },
    })

    if (!question) {
      throw new Error("Unable to find question")
    }

    const correctValue =
      action_name === "mark_correct"
        ? FeedbackState.CORRECT
        : FeedbackState.INCORRECT
    await prisma.question.update({
      data: {
        feedbackState: correctValue,
      },
      where: { id: question.id },
    })
  } else {
    // actionName === 'create'
    // If there isn't a question, create one
    if (q) {
      questions = await findOrCreateQuestion(userId, q, questionGroup.id)
    } else {
      // Just used to create a new QuestionGroup
      questions = [] as QuestionInBrowser[]
    }
  }

  if (q) {
    // TODO questionID
    return redirect(
      `/admin/${questionGroup.id}/chart/raw?q=${encodeURIComponent(q || "")}`
    )
  } else {
    return redirect(`/admin/${questionGroup.id}/chart/raw`)
  }
}

export let loader: LoaderFunction = async ({
  params,
  request,
}): Promise<LoaderData> => {
  const userId = await requireUserId(request)

  // extract natural language query from query params
  const { q } = zx.parseQuery(request, { q: z.string().optional() })

  // extract group from path params
  const { questionGroupId } = zx.parseParams(params, {
    questionGroupId: zx.NumAsString,
  })

  // make sure questionGroup exists
  let questionGroup = await findOrCreateQuestionGroup(userId, questionGroupId)

  let questions: QuestionInBrowser[]
  let question: QuestionInBrowser | null
  if (q) {
    // If there isn't a question, create one
    questions = await findOrCreateQuestion(userId, q, questionGroup.id)

    // grab the latest question
    question = questions[questions.length - 1]
  } else {
    questions = [] as QuestionInBrowser[]
    question = null
  }

  let resultJson

  if (question) {
    const dataSourceId = 1
    const dataSource = fakeDataSource()

    try {
      const sql = await questionToSql(dataSource.id, question)
      log.debug("sql from python", { sql })

      const results = await runQuery(dataSource, sql)

      // prettify the resulting JSON
      resultJson = beautify(results, null!, 2, 100)
    } catch (e) {
      console.error(e)
      resultJson = beautify({ message: e!.toString(), error: e }, null!, 2, 100)
    }
  } else {
    resultJson = ""
  }

  return {
    questions,
    questionGroupId: questionGroupId,
    latestResult: resultJson,
  }
}

function QueryHeader({ data }: { data: LoaderData }) {
  const params = useParams()

  const [searchParams] = useSearchParams()
  const q = searchParams.get("q")

  const questionGroupId = params.questionGroupId
  if (!questionGroupId) {
    throw new Error("No question group id was provided")
  }

  let currentQuestion: QuestionInBrowser | null
  let questions: QuestionInBrowser[]
  if (data && q) {
    questions = [...data.questions] // shallow copy to prevent issues
    if (questions.length === 0) {
      currentQuestion = null
    } else {
      let currentQuestionIndex = questions.findIndex((qu) => qu.question === q)
      if (currentQuestionIndex === -1) {
        currentQuestionIndex = questions.length - 1
      }
      currentQuestion = questions.splice(currentQuestionIndex, 1)[0]
    }
  } else {
    questions = []
    currentQuestion = null
  }

  const [question, setQuestion] = useState(currentQuestion?.question || "")
  const [getQuery, setQuery] = useState(currentQuestion?.userSql || "")

  useEffect(() => {
    // update the userSql when it updates from the backend
    const userSql = currentQuestion?.userSql
    if (userSql) {
      setQuery(userSql)
    }

    const loaderQuestion = currentQuestion?.question
    if (loaderQuestion) {
      setQuestion(loaderQuestion)
    }
  }, [
    currentQuestion,
    q,
    currentQuestion?.question,
    currentQuestion?.userSql,
    data?.questionGroupId,
  ])

  const submitSqlQuery = useSubmit()

  // called when the user does SHIFT+Enter, updates the sql in the db
  // which will run the new query
  const updateSqlQuery = () => {
    if (currentQuestion) {
      submitSqlQuery(
        {
          action_name: "update",
          questionGroupId: questionGroupId,
          id: currentQuestion.id.toString(),
          q: currentQuestion.question,
          userSql: getQuery,
        },
        { method: "post" }
      )
    }
  }

  const navigation = useNavigation()

  let previousQuestions
  if (questions) {
    previousQuestions = questions.reverse().map((q, i) => {
      return (
        <tr key={q.question}>
          <td key={`td-${q.question}`}>{q.question}</td>
        </tr>
      )
    })
  } else {
    previousQuestions = <></>
  }

  return (
    <>
      <Header height={250} p="0" m="0">
        <Grid sx={{ height: "100%" }} p="0" m="0">
          <Grid.Col span={5} p="lg">
            <Stack justify="space-between" sx={{ height: "100%" }}>
              <Box>
                <Form method="post">
                  <Flex>
                    <input
                      type="hidden"
                      name="questionGroupId"
                      value={questionGroupId}
                    />
                    <TextInput
                      size="lg"
                      w="100%"
                      name="q"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                    />
                    <Button size="lg" type="submit">
                      &gt;
                    </Button>
                    {navigation.state === "submitting" && (
                      <Loader size="xl" variant="bars" p="10px" />
                    )}
                  </Flex>
                </Form>

                <Box sx={{ height: "90px", overflowY: "auto" }}>
                  <Table p="sm">
                    <tbody>{previousQuestions}</tbody>
                  </Table>
                </Box>
              </Box>

              <Flex>
                <Box w="100%">
                  <Form method="post" action="/admin">
                    <Button type="submit" w="100%">
                      New Question
                    </Button>
                  </Form>
                </Box>
                <Box w="100%">
                  <Form method="post">
                    <input
                      type="hidden"
                      name="action_name"
                      value="mark_correct"
                    />
                    <input
                      type="hidden"
                      name="questionGroupId"
                      value={questionGroupId}
                    />
                    <Button w="100%" type="submit" color="green">
                      {currentQuestion?.feedbackState === FeedbackState.CORRECT
                        ? "✓"
                        : ""}
                      Mark Correct
                    </Button>
                  </Form>
                </Box>
                <Box w="100%">
                  <Form method="post">
                    <input
                      type="hidden"
                      name="action_name"
                      value="mark_incorrect"
                    />
                    <input
                      type="hidden"
                      name="questionGroupId"
                      value={questionGroupId}
                    />
                    <Button w="100%" type="submit" color="red">
                      {currentQuestion?.feedbackState ===
                      FeedbackState.INCORRECT
                        ? "✓"
                        : ""}
                      Mark Incorrect
                    </Button>
                  </Form>
                </Box>
              </Flex>
            </Stack>
          </Grid.Col>
          <Grid.Col span={1} p="lg"></Grid.Col>
          <Grid.Col span={6} p="0" sx={{ position: "relative" }}>
            <CodeMirror
              height="250px"
              value={getQuery}
              extensions={[sql({}), EditorView.lineWrapping]}
              onChange={(e) => setQuery(e)}
              onKeyDownCapture={(e) => {
                // shift+enter to edit the query
                if (e.shiftKey && e.key === "Enter") {
                  e.stopPropagation()
                  e.preventDefault()
                  updateSqlQuery()
                }
              }}
            />

            <Box
              sx={{
                position: "absolute",
                bottom: "0px",
                left: "0px",
                right: "0px",
              }}
            >
              <Text c="dimmed" align="center">
                <span
                  style={{
                    padding: "5px",
                    backgroundColor: "rgba(128,128,128,0.1)",
                  }}
                >
                  Press Shift+Enter to executre an updated query
                </span>
              </Text>
            </Box>
          </Grid.Col>
        </Grid>
      </Header>
    </>
  )
}

export default function QuestionGroup() {
  let data = useLoaderData<LoaderData>()
  const params = useParams()

  return (
    <>
      <AppShell
        padding="md"
        header={<QueryHeader data={data} />}
        styles={(theme) => ({
          main: {
            backgroundColor:
              theme.colorScheme === "dark"
                ? theme.colors.dark[8]
                : theme.colors.gray[0],
          },
        })}
      >
        <Outlet />
        <Footer />
      </AppShell>
    </>
  )
}

export function CatchBoundary() {
  const caught = useCatch()
  return <h1>Caught error: {caught.statusText}</h1>
}
