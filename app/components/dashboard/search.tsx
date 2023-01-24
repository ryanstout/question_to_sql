import { z } from "zod"
import { zx } from "zodix"
import { useState, useEffect } from "react"

import { ActionArgs, LoaderFunction, redirect, LoaderArgs, json } from "@remix-run/node"
import { Form, useLoaderData, useLocation, useSearchParams } from "@remix-run/react"

import { 
    Center,
    Loader,
     TextInput,
     Title,
     Grid
} from "@mantine/core"

import { Hero } from "~/routes/hero"
import { requireUserId } from "~/session.server"
import { useOptionalUser } from "~/utils"

import { IconSearch } from '@tabler/icons';

type LoaderData = {
  id: string
} | null

// export let loader: LoaderFunction = async ({
//   params,
//   request,
// }): Promise<LoaderData> => {
//   const userId = await requireUserId(request)
//   console.log("REQUEST", request);
//   console.log("PARAMS", params);
  
//   return {
//     id: "EXAMPLE"
//   }
// }


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

    useEffect(() => {
      setFormSubmit(false)
    }, [
      formSubmit
    ])


  return (
    <>
      <main>
          <Grid>
              <Grid.Col span={4} offset={4}>
                <Form 
                    action="/query" method="post"
                    onSubmit={(e) => setFormSubmit(true)}
                    >
                        <TextInput
                        width={100}
                        name="questionText"
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
