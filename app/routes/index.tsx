import { HeaderMenu } from "./headerMenu"
import { useState } from "react"

import { Link } from "@remix-run/react"

import { useOptionalUser } from "~/utils"

export default function Index() {
  const user = useOptionalUser()
  const [question, setQuestion] = useState("")

  console.log("user: ", user)
  return (
    <>
      <HeaderMenu user={user} />
      <main>
        <Link to="/query">Get Started</Link>
      </main>
    </>
  )
}
