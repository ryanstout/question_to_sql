#!/usr/bin/env node
import {
  getResultsFromQuestion,
  processQuestion,
  updateQuestion,
} from "../app/lib/question.server"

import { log } from "~/lib/logging.server"

async function main() {
  log.debug("Asking example question...")
  const dataSourceId = 1
  const userId = 1
  const questionResult = await processQuestion(
    userId,
    dataSourceId,
    "What is the total number of orders?"
  )
  log.debug("Question answered...")

  console.log(questionResult)

  // now let's try updating a question
  const updatedQuestion = await updateQuestion(
    questionResult.question,
    "SELECT * FROM customers LIMIT 10"
  )
  log.debug("updated question")
  console.log(updatedQuestion)

  // now let's try just getting the results from an existing question
  const results = await getResultsFromQuestion({
    questionRecord: questionResult.question,
  })
  log.debug("got results from question")
  console.log(results)

  // try getting the results just from the question ID
  const resultsFromQuestion = await getResultsFromQuestion({
    questionId: questionResult.question.id,
  })
  debugger
}

main()
