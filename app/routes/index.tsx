import AppFooter from "../components/dashboard/footer"
import { HeaderMenu } from "../components/dashboard/headerMenu"
import { useState } from "react"
import { z } from "zod"
import { zx } from "zodix"

import { json } from "@remix-run/node"
import type { ActionArgs } from "@remix-run/node"
import { Link, Outlet, useActionData, useLocation } from "@remix-run/react"

import { AppShell } from "@mantine/core"

import Search from "~/components/dashboard/search"
import QueryFeedback from "~/components/dashboard/queryFeedback"
import { questionToSql } from "~/lib/question.server"
import { useOptionalUser } from "~/utils"

export const action = async ({ request }: ActionArgs) => {
  const { q } = await zx.parseForm(request, {
    q: z.string().optional(),
  })

  const sql = await questionToSql(q)

  return json({ q, sql })
}

export default function Index() {
  const user = useOptionalUser()
  const loader = useActionData()
  console.log(loader);
  return (
    <AppShell footer={<AppFooter />}>
      <HeaderMenu user={user} />
      <Search question={loader ? loader.q : ""} />
      <QueryFeedback feedback = {loader ? loader : {}}/>
    </AppShell>
  )
}
