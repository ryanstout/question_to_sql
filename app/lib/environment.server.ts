import invariant from "tiny-invariant"

import { log } from "~/lib/logging.server"

export function isProduction() {
  return process.env.NODE_ENV === "production"
}

export function isTest() {
  return process.env.NODE_ENV === "test"
}

export function isMockedPythonServer() {
  const isMocked = process.env.MOCKED_QUESTION_RESPONSE === "true"

  invariant(
    !isMocked || !isProduction(),
    "python server mocking is enabled in production"
  )

  return isMocked
}

log.debug("environment", {
  mocked: isMockedPythonServer(),
  production: isProduction(),
})
