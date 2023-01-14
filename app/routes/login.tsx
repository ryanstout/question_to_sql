import type { ActionArgs, LoaderArgs, MetaFunction } from "@remix-run/node";
import { json, redirect } from "@remix-run/node";
import { Link, useSearchParams } from "@remix-run/react";
import { z } from "zod";
import { prisma } from "~/db.server";

import {
  Anchor, Button, Checkbox, Container,
  Group, Paper, PasswordInput, Text, TextInput, Title
} from '@mantine/core';
import { withZod } from "@remix-validated-form/with-zod";


import { ValidatedForm, validationError } from "remix-validated-form";
import { Field } from "~/components/field";
import { verifyLogin } from "~/models/user.server";
import { createUserSession, getUserId } from "~/session.server";

export async function loader({ request }: LoaderArgs) {
  const userId = await getUserId(request);
  if (userId) return redirect("/");
  return json({});
}

export const validator = withZod(
  z.object({
    email: z
      .string()
      .min(1, { message: "Email is required" }),
    password: z
      .string()
      .min(1, { message: "Password is too short" }),
  })
);


export async function action({ request }: ActionArgs) {
  const formData = await request.formData()
  const data = await validator.validate(formData);
  if (data.error) { return validationError(data.error); }

  const email = data.data.email

  const userExists = await prisma.user.findUnique({
    select: { id: true },
    where: { email },
  })

  if (!userExists) {
    return validationError(
      {
        fieldErrors: {
          email: "No user with this email was found",
        },
      }
    )

  }
  const user = await verifyLogin(data.data.email, data.data.password);

  if (!user) {
    return validationError(
      {
        fieldErrors: {
          password: "Password was incorrect",
        },
      }
    )
  }

  const redirectTo = formData.get("redirectTo") || '/'

  if (typeof redirectTo !== 'string') {
    throw new Error("Invalid redirect")
  }

  return createUserSession({
    request,
    userId: user.id,
    redirectTo,
    remember: formData.get("remember") === "on" ? true : false,
  });
}

export const meta: MetaFunction = () => {
  return {
    title: "Login",
  };
};



export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const redirectTo = searchParams.get("redirectTo") || "/";

  return (
    <Container size={420} my={40}>
      <Title
        align="center"
        sx={(theme) => ({ fontFamily: `Greycliff CF, ${theme.fontFamily}`, fontWeight: 900 })}
      >
        Welcome back!
      </Title>
      <Text color="dimmed" size="sm" align="center" mt={5}>
        Do not have an account yet?{' '}
        <Text component={Link} to="/signup" size="sm">
          Create account
        </Text>
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <ValidatedForm validator={validator} method="post" action="/login">
          <input type="hidden" name="redirectTo" value={redirectTo} />
          <Field component={TextInput} name="email" label="Email" placeholder="you@mantine.dev" required />
          <Field component={PasswordInput} name="password" label="Password" placeholder="Your password" required mt="md" />
          <Group position="apart" mt="lg">
            <Checkbox name="remember" label="Remember me" sx={{ lineHeight: 1 }} />
            <Anchor<'a'> onClick={(event) => event.preventDefault()} href="#" size="sm">
              Forgot password?
            </Anchor>
          </Group>
          <Button type="submit" fullWidth mt="xl">
            Sign in
          </Button>
        </ValidatedForm>
      </Paper>
    </Container>

  );
}
