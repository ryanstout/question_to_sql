#!/usr/bin/env node
import { processQuestion } from "../app/lib/question.server"

import { log } from "~/lib/logging.server"

log.debug("Asking example question...")
processQuestion(1, 1, "What is the total number of orders?").then((r) => {
  log.debug("Question answered...")
  console.log(r)
})
