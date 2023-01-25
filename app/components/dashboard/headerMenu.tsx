import {
  Box,
  Button, createStyles, Grid,
  Header,
  Image
} from "@mantine/core"
import { Form } from "@remix-run/react"
import {
  IconLogout
} from "@tabler/icons"
import Logo from "~/assets/images/LogoHorizontal.svg"
import { useOptionalUser } from "~/utils"

const useStyles = createStyles((theme) => ({
  link: {
    display: "flex",
    alignItems: "center",
    height: "100%",
    paddingLeft: theme.spacing.md,
    paddingRight: theme.spacing.md,
    textDecoration: "none",
    color: theme.colorScheme === "dark" ? theme.white : theme.black,
    fontWeight: 500,
    fontSize: theme.fontSizes.sm,

    [theme.fn.smallerThan("sm")]: {
      height: 42,
      display: "flex",
      alignItems: "center",
      width: "100%",
    },

    ...theme.fn.hover({
      backgroundColor:
        theme.colorScheme === "dark"
          ? theme.colors.dark[6]
          : theme.colors.gray[0],
    }),
  }
}))

export default function HeaderMenu() {

  const user = useOptionalUser();

  let loginMenu
  if (user) {
    loginMenu = (
      <Box mt={5} ta="right">
        <Form action="/logout" method="post">
          <Button variant="outline" type="submit">Logout&nbsp;<IconLogout/></Button>
        </Form>
        <Box my={3}>
          <i>{user.email}</i>
        </Box>
      </Box>
    )
  }

  return (
    <Box pb={70}>
      <Header height={80} px="md">
        <Grid>
        <a href="/"><Image height={70} width={180} mt={11} src={Logo} /></a>
        <Grid.Col span={1} offset={9}>
        {loginMenu}
        </Grid.Col>
        </Grid>
      </Header>

    </Box>
  )
}
