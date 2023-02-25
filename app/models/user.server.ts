import bcrypt from "bcryptjs"

import { redirect } from "@remix-run/node"

import type { Password, User } from "@prisma/client"

import { prisma } from "~/db.server"
import { getUser } from "~/session.server"
import { isAdmin } from "~/utils"

export type { User } from "@prisma/client"

export async function getUserById(id: User["id"]) {
  return prisma.user.findUnique({
    where: { id },
    include: {
      business: {
        include: {
          dataSources: {
            select: {
              // do NOT include credentials! This could be accidentally exposed to a loader
              name: true,
              id: true,
            },
          },
        },
      },
    },
  })
}

export async function getUserByEmail(email: User["email"]) {
  return prisma.user.findUnique({ where: { email } })
}

export async function createUser(
  email: User["email"],
  password: string,
  name: string
) {
  const hashedPassword = await bcrypt.hash(password, 10)

  return prisma.user.create({
    data: {
      email,
      name,
      password: {
        create: {
          hash: hashedPassword,
        },
      },
    },
  })
}

export async function deleteUserByEmail(email: User["email"]) {
  return prisma.user.delete({ where: { email } })
}

export async function verifyLogin(
  email: User["email"],
  password: Password["hash"]
) {
  const userWithPassword = await prisma.user.findUnique({
    where: { email },
    include: {
      password: true,
    },
  })

  if (!userWithPassword || !userWithPassword.password) {
    return null
  }

  const isValid = await bcrypt.compare(password, userWithPassword.password.hash)

  if (!isValid) {
    return null
  }

  const { password: _password, ...userWithoutPassword } = userWithPassword

  return userWithoutPassword
}

export async function requireAdmin(request: Request) {
  const user = await getUser(request)

  if (!user || !isAdmin(user)) {
    throw redirect(`/login`)
  }

  return user
}
