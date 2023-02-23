import invariant from "tiny-invariant"

import { PrismaClient } from "@prisma/client"

import { isProduction, isTest } from "~/lib/environment"

import * as Sentry from "@sentry/remix"

let prisma: PrismaClient

declare global {
  var __db__: PrismaClient
}

function getClient() {
  let databaseUrl: URL

  if (isTest()) {
    const { TEST_DATABASE_URL } = process.env
    invariant(
      typeof TEST_DATABASE_URL === "string",
      "TEST_DATABASE_URL env var not set"
    )
    databaseUrl = new URL(TEST_DATABASE_URL)
  } else {
    const { DATABASE_URL } = process.env
    invariant(typeof DATABASE_URL === "string", "DATABASE_URL env var not set")
    databaseUrl = new URL(DATABASE_URL)
  }

  const isLocalHost = databaseUrl.hostname === "localhost"

  const PRIMARY_REGION = isLocalHost ? null : process.env.PRIMARY_REGION
  const FLY_REGION = isLocalHost ? null : process.env.FLY_REGION

  const isReadReplicaRegion = !PRIMARY_REGION || PRIMARY_REGION === FLY_REGION

  if (!isLocalHost) {
    databaseUrl.host = `${FLY_REGION}.${databaseUrl.host}`
    if (!isReadReplicaRegion) {
      // 5433 is the read-replica port
      databaseUrl.port = "5433"
    }
  }

  console.log(
    `🔌 setting up prisma client to ${databaseUrl.host} with dbname ${databaseUrl.pathname}`
  )
  // NOTE: during development if you change anything in this function, remember
  // that this only runs once per server restart and won't automatically be
  // re-run per request like everything else is. So if you need to change
  // something in this file, you'll need to manually restart the server.
  const client = new PrismaClient({
    datasources: {
      db: {
        url: databaseUrl.toString(),
      },
    },
  })

  // connect eagerly
  client.$connect()

  // type arguments = Parameters<typeof client.evaluationQuestionGroup.update>
  // type dataArgument = arguments[0]["data"]
  // const updateCommand = async (data: dataArgument) => {
  //   debugger
  //   return await client.evaluationQuestionGroup.update({
  //     where: { id: this.id },
  //     data: data,
  //   })
  // }

  // // now, let's add some methods that just should have existed already
  // const xclient = client.$extends({
  //   // name: 'customExtensions',
  //   model: {
  //     evaluationQuestionGroup: {
  //       updateCommand
  //     }
  //   },
  // })

  return client
}

// this is needed because in development we don't want to restart
// the server with every change, but we want to make sure we don't
// create a new connection to the DB with every change either.
// in production we'll have a single connection to the DB.
if (isProduction()) {
  prisma = getClient()
} else {
  if (!global.__db__) {
    global.__db__ = getClient()
  }
  prisma = global.__db__
}

// NOTE sentry setup is on the server so we can pass the prisma reference
if (isProduction()) {
  const { SENTRY_DSN } = process.env
  invariant(SENTRY_DSN, "SENTRY_DSN is not defined")

  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    tracesSampleRate: 0.1,
    integrations: [new Sentry.Integrations.Prisma({ client: prisma })],
    beforeSendTransaction(event) {
      if (event.transaction === "/healthcheck") {
        return null
      }
      return event
    },
  })
}

export { prisma }
