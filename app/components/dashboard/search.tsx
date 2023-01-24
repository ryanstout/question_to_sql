import { IconSearch } from "@tabler/icons"
import { useEffect, useState } from "react"
import { z } from "zod"
import { zx } from "zodix"

import type { ActionArgs } from "@remix-run/node"
import { LoaderArgs, LoaderFunction, json, redirect } from "@remix-run/node"
import {
  Form,
  useLoaderData,
  useLocation,
  useSearchParams,
} from "@remix-run/react"

import { Center, Grid, Loader, TextInput, Title } from "@mantine/core"

import { Hero } from "~/routes/hero"
import { requireUserId } from "~/session.server"
import { useOptionalUser } from "~/utils"

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

export default function Search({ question }: { question: string }) {
  const user = useOptionalUser()

  if (!question) {
    question = "How many cameras did we sell?"
  }

  return (
    <>
      <main>
        <Grid>
          <Grid.Col span={4} offset={4}>
            <Form action="?index" method="post">
              <TextInput
                width={100}
                name="q"
                defaultValue={question}
                icon={<IconSearch size={18} />}
              />
            </Form>
          </Grid.Col>
        </Grid>
      </main>
    </>
  )
}
