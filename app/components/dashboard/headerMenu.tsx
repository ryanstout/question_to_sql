import { Form } from "@remix-run/react"

import { Box, Button, Grid, Header, Image } from "@mantine/core"

import Logo from "~/assets/images/LogoHorizontal.svg"
import { useOptionalUser } from "~/utils"

import { IconLogout } from "@tabler/icons"

export default function HeaderMenu() {
  const user = useOptionalUser()

  let loginMenu
  if (user) {
    loginMenu = (
      <Box mt={15} ta="right">
        <Form action="/logout" method="post">
          <Button variant="outline" type="submit">
            Logout&nbsp;
            <IconLogout />
          </Button>
        </Form>
      </Box>
    )
  }

  return (
    <Header height={80} px="md">
      <Grid>
        <a href="/">
          <Image height={70} width={180} mt={11} src={Logo} />
        </a>
        <Grid.Col span={1} offset={9}>
          {loginMenu}
        </Grid.Col>
      </Grid>
    </Header>
  )
}
