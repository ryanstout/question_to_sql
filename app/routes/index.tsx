
import {
  AppShell
} 
from "@mantine/core"

import { HeaderMenu } from "../components/dashboard/headerMenu"
import Search from "../components/dashboard/search"
import AppFooter  from "../components/dashboard/footer"
import { useState } from "react"

import { Link } from "@remix-run/react"

import { useOptionalUser } from "~/utils"

export default function Index() {
  const user = useOptionalUser()
  const [question, setQuestion] = useState("")

  
  return (
    <AppShell
      footer={
        <AppFooter/>
      }
    >
      <HeaderMenu user={user} />
      <Search/>
        
    </AppShell>
  )
}
