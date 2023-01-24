import { z } from "zod"
import { zx } from "zodix"

import { json, redirect } from "@remix-run/node"
import {
  Form,
  useLoaderData,
  useLocation,
  useSearchParams,
} from "@remix-run/react"

import Search from "~/components/dashboard/search"
import { prisma } from "~/db.server"
import {
  EnhanceSqlQuery,
  GenerateSqlQuery,
} from "~/models/language_model/query_generator.server"

export const loader = async () => {
  console.log("HERE")
  // const location = useLocation()
  // let params = new URLSearchParams(location.search);
  // console.log("location", location);
  // console.log("PARAMS", params.getAll("id"));
  return json({ ok: true })
}

export async function action({ request }: ActionArgs) {
  const { questionText } = await zx.parseForm(request, {
    questionText: z.string().optional(),
  })

  let codexSql = await generateQuestionSQL(questionText || "")
  let question = await createQuestion(questionText || "", 1, codexSql, 1)

  if (question) {
    return redirect(`/?id=${question.id}`)
  } else {
    return redirect("/")
  }
}

//   async function generateQuestionSQL(questionText: string){
//     console.log(questionText);
//     let codexSql = await GenerateSqlQuery(questionText)
//     codexSql = await EnhanceSqlQuery(codexSql)
//     return codexSql;
//   }

//   async function createQuestion(
//     questionText: string,
//     questionGroupId: number,
//     codexSql: string,
//     userId?: number
//   ) {

//     let question = await prisma.question.create({
//       data: {
//         question: questionText,
//         userId: userId,
//         questionGroupId: questionGroupId,
//         userSql: codexSql,
//         codexSql: codexSql,
//         feedbackState: 'UNKNOWN'
//       },
//     })

//     return question
//   }

export default function QuerySearch() {
  const ok = useLoaderData()
  console.log("LOGGING IN COMPONENT", ok)

  return <Search />
}
