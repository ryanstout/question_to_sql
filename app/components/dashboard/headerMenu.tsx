import { $path } from "remix-routes"

import { Form } from "@remix-run/react"

import { Button, Group, Header, Image } from "@mantine/core"

import type { User } from "@prisma/client"

import Logo from "~/assets/images/LogoHorizontal.svg"
import { useOptionalUser } from "~/utils"

import { IconLogout } from "@tabler/icons-react"

function isAdmin(user: User) {
  return user.email.endsWith("@knolbe.com")
}

export default function HeaderMenu() {
  const user = useOptionalUser()

  // TODO second empty param in $path is required, wait before rolling this out https://github.com/yesmeck/remix-routes/issues/43 */
  const loginMenu = !user ? null : (
    <Form action={$path("/logout", {})} method="post">
      <Button variant="outline" type="submit">
        Logout&nbsp;
        <IconLogout />
      </Button>
    </Form>
  )

  const adminMenu =
    user && isAdmin(user) ? (
      <>
        <Button component="a" href={$path("/internal", {})}>
          Group Questions
        </Button>
        <Button component="a" href={$path("/internal/group", {})}>
          Evaluation Groups
        </Button>
      </>
    ) : null

  return (
    <Header height={80} px="md">
      <>
        <a style={{ float: "left" }} href="/">
          <Image height={70} width={180} mt={5} src={Logo} />
        </a>
        <Group mt={20} position="right">
          {adminMenu}
          {loginMenu}
        </Group>
      </>
    </Header>
  )
}
