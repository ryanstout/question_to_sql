// import { Connection } from 'postgresql-client';
import { sql } from "@codemirror/lang-sql"
import { EditorView } from "@codemirror/view"
import type { Question, User } from "@prisma/client"
import CodeMirror from "@uiw/react-codemirror"
import beautify from "json-beautify"
import { useEffect, useState } from "react"
import { z } from "zod"
import { zx } from "zodix"

import { ActionArgs, LoaderFunction, redirect } from "@remix-run/node"
import {
  Form,
  Outlet,
  useCatch,
  useLoaderData,
  useLocation,
  useNavigation,
  useParams,
  useSubmit,
} from "@remix-run/react"

import {
  AppShell,
  Box,
  Button,
  Flex,
  Grid,
  Header,
  List,
  Loader,
  Navbar,
  Stack,
  Table,
  Text,
  TextInput,
} from "@mantine/core"

import { prisma } from "~/db.server"
import {
  EnhanceSqlQuery,
  GenerateSqlQuery,
} from "~/models/language_model/query_generator.server"
import { UserDb } from "~/models/user_db2.server"
import { Footer } from "~/routes/footer"
import { requireUserId } from "~/session.server"
import { toNum } from "~/utils"

type QuestionInBrowser = Pick<
  Question,
  "id" | "question" | "questionGroupId" | "userSql" | "correctState"
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
    // create the question if it doesn't exist

    // We need to generate the sql for the query since its new
    let codexSql = await GenerateSqlQuery(q)
    codexSql = await EnhanceSqlQuery(codexSql)

    // create the new query
    question = await prisma.question.create({
      data: {
        questionGroupId: questionGroupId,
        question: q,
        userId: userId,
        userSql: codexSql,
        codexSql: codexSql,
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
      correctState: true,
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

    const correctValue = action_name === "mark_correct" ? 1 : 0
    await prisma.question.update({
      data: { correctState: correctValue },
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
    return redirect(
      `/query/${questionGroup.id}/chart/raw?q=${encodeURIComponent(q || "")}`
    )
  } else {
    return redirect(`/query/${questionGroup.id}/chart/raw`)
  }
}

export let loader: LoaderFunction = async ({
  params,
  request,
}): Promise<LoaderData> => {
  const userId = await requireUserId(request)

  const { q } = zx.parseQuery(request, { q: z.string().optional() })
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
    try {
      const db = new UserDb()
      await db.connect()
      const result = await db.query(question.userSql)
      await db.close()
      resultJson = beautify(result.results, null!, 2, 100)
    } catch (e) {
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

  let location = useLocation()
  const urlParams = new URLSearchParams(location.search)
  const q = urlParams.get("q")

  const questionGroupId = params.questionGroupId
  if (!questionGroupId) {
    throw new Error("No question group id was provided")
  }

  let currentQuestion: QuestionInBrowser | null
  let questions: QuestionInBrowser[]
  if (data && q) {
    questions = [...data.questions]
    if (questions.length === 0) {
      currentQuestion = null
    } else {
      let currentQuestionIndex = questions.findIndex((question) => {
        return question.question === q
      })
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
                  <Form method="post" action="/query">
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
                      {currentQuestion?.correctState === 1 ? "✓" : ""}
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
                      {currentQuestion?.correctState === 0 ? "✓" : ""}
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

// export function links() {
//     return [{ rel: "stylesheet", href: styles }];
// }

export default function QuestionGroup() {
  let data = useLoaderData<LoaderData>()
  const params = useParams()

  return (
    // <Flex direction="column" sx={{ height: '100vh' }}>
    //     <QueryHeader q={q} query={query} />
    //     <Box sx={{ overflowY: 'scroll' }}>
    //         <Grid>
    //             <Grid.Col span={2}>
    //                 <Box>
    //                     <Navbar width={{ base: 300 }} height="100%" p="xs">
    //                         <h2>Side navbar</h2>
    //                     </Navbar>

    //                 </Box>
    //             </Grid.Col>
    //             <Grid.Col span={10}>
    //                 <Box>
    //                     <Outlet />
    //                     <Footer />
    //                 </Box>
    //             </Grid.Col>
    //         </Grid>

    //     </Box>
    // </Flex>

    <>
      <AppShell
        padding="md"
        navbar={
          <Navbar width={{ base: 300 }} height="100%" p="xs">
            <h2>Side</h2>
          </Navbar>
        }
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
