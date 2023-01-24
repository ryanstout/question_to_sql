import { useState } from "react"
import { z } from "zod"
import { zx } from "zodix"

import { ActionArgs, LoaderFunction, redirect } from "@remix-run/node"
import { Form } from "@remix-run/react"

import { 
    Center,
    Loader,
     TextInput,
     Title,
     Grid
} from "@mantine/core"

import { prisma } from "~/db.server"
import { Hero } from "~/routes/hero"
import { findOrCreateQuestionGroup } from "~/routes/query/$questionGroupId"
import { requireUserId } from "~/session.server"
import { useOptionalUser } from "~/utils"
import queryRunner from "~/lib/query-runner"
import {
  EnhanceSqlQuery,
  GenerateSqlQuery
} from "~/models/language_model/query_generator.server"

import { IconSearch } from '@tabler/icons';

async function generateQuestionSQL(questionText: string){
  console.log(questionText);
  let codexSql = await GenerateSqlQuery(questionText)
  codexSql = await EnhanceSqlQuery(codexSql)
  return codexSql;
}

async function createQuestion(
  questionText: string,
  questionGroupId: number,
  codexSql: string,
  userId?: number
) {

  let question = await prisma.question.create({
    data: {
      question: questionText,
      userId: userId,
      questionGroupId: questionGroupId,
      userSql: codexSql,
      codexSql: codexSql,
      feedbackState: 'UNKNOWN'
    },
  })

  return question
}

export default function Search() {
  
  const user = useOptionalUser();
  const [questionText, setQuestionText] = useState("How many cameras did we sell?")
  const [formSubmit, setFormSubmit] = useState(false)
  
  let loaderDisplay;
  if(formSubmit){
    loaderDisplay = (
      <Loader size="xs"/>
      )
    }
    
  const HandleSubmit = async () => {
    setFormSubmit(true);
    let codexSql = await generateQuestionSQL(questionText);
    console.log(codexSql);
    let question = await createQuestion(questionText, 1, codexSql, user?.id);
    console.log(question)
  }

  return (
    <>
      <main>
          <Grid>
              <Grid.Col span={4} offset={4}>
                <Form 
                    onSubmit={(e) => HandleSubmit()}
                    >
                        <TextInput
                        width={100}
                        value={questionText}
                        icon={<IconSearch size={18} />} 
                        rightSection={loaderDisplay}
                        onChange={(e) => setQuestionText(e.target.value)}
                    />
                </Form>
              </Grid.Col>
          </Grid>
      </main>
    </>
  )
}
