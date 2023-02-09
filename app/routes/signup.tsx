import { ValidatedForm, validationError } from "remix-validated-form"
import { z } from "zod"

import { json } from "@remix-run/node"
import { Link } from "@remix-run/react"
import type { ActionArgs } from "@remix-run/server-runtime"
import { withZod } from "@remix-validated-form/with-zod"

import {
  Anchor,
  Button,
  Container,
  Paper,
  PasswordInput,
  Text,
  TextInput,
  Title,
} from "@mantine/core"

import { PasswordWithStrength } from "~/components/PasswordWithStrength"
import { Field } from "~/components/field"
import { createUser, getUserByEmail } from "~/models/user.server"
import { createUserSession } from "~/session.server"
import { safeRedirect } from "~/utils"

var passwordCheck = /^(?=.*[0-9])(?=.*[!@#$%^&*])[a-zA-Z0-9!@#$%^&*]{6,250}$/

export const validator = withZod(
  z
    .object({
      email: z.string().email(),
      name: z.string().min(3, "Name must be at least 3 characters"),
      password: z.string().min(6, { message: "Password is required" }),
      confirm: z.string(),
      redirectTo: z.string().optional(),
    })
    .refine((data) => data.password === data.confirm, {
      message: "Password doesn't match",
      path: ["confirm"],
    })
    .refine((data) => passwordCheck.test(data.password), {
      message:
        "Password be at least 6 characters, include a number, lowercase letter, uppercase letter, and a special character",
      path: ["password"],
    })
)

export async function action({ request }: ActionArgs) {
  const data = await validator.validate(await request.formData())
  if (data.error) {
    return validationError(data.error)
  }

  const redirectTo = safeRedirect(data.data.redirectTo, "/")

  const existingUser = await getUserByEmail(data.data.email)
  if (existingUser) {
    return json(
      {
        errors: {
          email: "A user already exists with this email",
          password: null,
        },
      },
      { status: 400 }
    )
  }

  const user = await createUser(
    data.data.email,
    data.data.password,
    data.data.name
  )

  return createUserSession({
    request,
    userId: user.id,
    remember: false,
    redirectTo,
  })
}

export default function Join2() {
  return (
    <Container size={420} my={40}>
      <Title
        align="center"
        sx={(theme) => ({
          fontFamily: `Greycliff CF, ${theme.fontFamily}`,
          fontWeight: 900,
        })}
      >
        Create an Account
      </Title>
      <Text color="dimmed" size="sm" align="center" mt={5}>
        Already have an account?{" "}
        <Anchor component={Link} to="/login" size="sm">
          Login here
        </Anchor>
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <ValidatedForm validator={validator} method="post">
          <Field
            component={TextInput}
            name="email"
            label="Email"
            placeholder="youremail@domain.com"
          />
          <Field
            component={TextInput}
            name="name"
            label="Full Name"
            placeholder="Your full name"
            mt="md"
          />
          <Field
            component={PasswordWithStrength}
            name="password"
            label="Password"
            placeholder="Your password"
            mt="md"
          />
          <Field
            component={PasswordInput}
            name="confirm"
            label="Confirm password"
            placeholder="Confirm your password"
            mt="md"
          />
          <Button type="submit" fullWidth mt="xl">
            Create Account
          </Button>
        </ValidatedForm>
      </Paper>
    </Container>
  )
}
