#!/usr/bin/env node
import { processQuestion } from "../app/lib/question.server"

console.log("let's go!")

processQuestion(1, 1, "What is the total number of orders?").then((r) => {
  console.log("complete!")
  console.log(r)
})
