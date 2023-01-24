import { ValidatedForm, validationError } from "remix-validated-form"
import { z } from "zod"

import type { ActionArgs, LoaderArgs, MetaFunction } from "@remix-run/node"
import { json, redirect } from "@remix-run/node"
import { Link, useSearchParams } from "@remix-run/react"
import { withZod } from "@remix-validated-form/with-zod"

import {
  Anchor,
  Button,
  Center,
  Checkbox,
  Container,
  Grid,
  Group,
  Image,
  Paper,
  PasswordInput,
  Text,
  TextInput,
  Title,
} from "@mantine/core"

import { Field } from "~/components/field"
import { prisma } from "~/db.server"
import { verifyLogin } from "~/models/user.server"
import { createUserSession, getUserId } from "~/session.server"

import Logo from "../assets/images/LogoVertical.svg"

export async function loader({ request }: LoaderArgs) {
  const userId = await getUserId(request)
  if (userId) return redirect("/")
  return json({})
}

export const validator = withZod(
  z.object({
    email: z.string().min(1, { message: "Email is required" }),
    password: z.string().min(1, { message: "Password is too short" }),
  })
)

export async function action({ request }: ActionArgs) {
  const formData = await request.formData()
  const data = await validator.validate(formData)
  if (data.error) {
    return validationError(data.error)
  }

  const email = data.data.email

  const userExists = await prisma.user.findUnique({
    select: { id: true },
    where: { email },
  })

  if (!userExists) {
    return validationError({
      fieldErrors: {
        email: "No user with this email was found",
      },
    })
  }
  const user = await verifyLogin(data.data.email, data.data.password)

  if (!user) {
    return validationError({
      fieldErrors: {
        password: "Password was incorrect",
      },
    })
  }

  const redirectTo = formData.get("redirectTo") || "/"

  if (typeof redirectTo !== "string") {
    throw new Error("Invalid redirect")
  }

  return createUserSession({
    request,
    userId: user.id,
    redirectTo,
    remember: formData.get("remember") === "on" ? true : false,
  })
}

export const meta: MetaFunction = () => {
  return {
    title: "Login",
  }
}

export default function LoginPage() {
  const [searchParams] = useSearchParams()
  const redirectTo = searchParams.get("redirectTo") || "/"

  return (
    <Container size={420} my={40}>
      <Title
        align="center"
        sx={(theme) => ({
          fontFamily: `Greycliff CF, ${theme.fontFamily}`,
          fontWeight: 900,
        })}
      >
        
      </Title>


      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <Image width="70%" style={{marginLeft: "25%"}} px={1} py={1} src={Logo} />
        <ValidatedForm validator={validator} method="post" action="/login">
          <input type="hidden" name="redirectTo" value={redirectTo} />
          <Field
            component={TextInput}
            name="email"
            label="Email"
            required
          />
          <Field
            component={PasswordInput}
            name="password"
            label="Password"
            required
            mt="md"
          />
          <Group position="apart" mt="lg">
            <Checkbox
              name="remember"
              label="Remember me"
              sx={{ lineHeight: 1 }}
            />
          </Group>
          <Button type="submit" fullWidth mt="xl" color="violet.7">
            Sign in
          </Button>
        </ValidatedForm>
      </Paper>
    </Container>
  )
}
