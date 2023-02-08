#!/usr/bin/env tsn
import { prisma } from "app/db.server"
import { log } from "app/lib/logging.server"

import { loadEnv } from "@remix-run/dev/dist/env"

// TODO wrap this up into a nice little config function
// TODO replace console.dir with custom method with better formatting
const util = require("util")
declare global {
  var dir: InstanceType<typeof Function>
  var toJson: InstanceType<typeof Function>
  var copyToClipboard: InstanceType<typeof Function>
  var getClassName: InstanceType<typeof Function>
}
// https://nodejs.org/api/util.html
util.inspect.defaultOptions.maxArrayLength = null
util.inspect.defaultOptions.colors = true
// TODO check if globals are accessible in a repl
global.dir = (ob: any) => process.stdout.write(util.inspect(ob))

function toJson(obj: any) {
  const jsonStr = JSON.stringify(obj, undefined, 2)
  copyToClipboard(jsonStr)
  console.log(jsonStr)
  return jsonStr
}
global.toJson = toJson

// copyToClipboard = (text) => {
function copyToClipboard(text: string) {
  require("child_process").spawnSync("/usr/bin/pbcopy", [], {
    env: {
      LC_CTYPE: "UTF-8",
    },
    input: text,
  })
}
global.copyToClipboard = copyToClipboard

// https://stackoverflow.com/questions/332422/get-the-name-of-an-objects-type
function getClassName(target) {
  const funcNameRegex = /function (.{1,})\(/
  const results = funcNameRegex.exec(getClassName.constructor.toString())
  return results && results.length > 1 ? results[1] : ""
}
global.getClassName = getClassName

// https://github.com/nodejs/node/issues/9617
function isDebugEnabled() {
  // even when using `node inspect` internally it gets transformed into --inspect-brk, which is why we check for this
  const inspectPassedOverCLI =
    process.execArgv.filter(
      (a) => a.includes("--inspect-brk") || a == "inspect"
    ).length > 0
  return require("inspector").url() !== undefined || inspectPassedOverCLI
}

async function repl(context?: any) {
  if (isDebugEnabled()) {
    // TODO `error` does not display any colored text... really?
    console.error("ERROR: Debug mode enabled, do not use repl!")
    return
  }

  await init()

  console.log("Starting REPL...")

  const repl = require("repl")
  const replServer = repl.start({
    prompt: "knolbe> ",
    input: process.stdin,
    output: process.stdout,
    useGlobal: true,
    preview: false,
  })

  // TODO tie into the ts-node repl
  // TODO remove all 'const ' from the input to avoid redeclaring variables error

  // list out all local variables
  replServer.defineCommand("vars", {
    help: "List all local variables",
    action: function () {
      this.displayPrompt()
      console.log(Object.keys(this.context))
    },
  })

  for (const key in context) {
    replServer.context[key] = context[key]
  }
}

// TODO I never was able to get this working...
// TODO `with` hack https://stackoverflow.com/questions/2051678/getting-all-variables-in-scope
function tsRepl(context?: any) {
  // https://typestrong.org/ts-node/api/index.html#createRepl
  const tsNode = require("ts-node")
  const repl = tsNode.createRepl()
  const service = tsNode.create({ ...repl.evalAwarePartialHost })
  repl.setService(service)
  repl.start()

  // for(const key in context) {
  //   repl.context[key] = context[key];
  // }
}

async function init() {
  log.info("Loading env...")
  await loadEnv("")
}

// the default DB client inspection output is so large that it makes it impossible to use the repl
prisma[Symbol.for("nodejs.util.inspect.custom")] = function (_depth, _options) {
  return "prisma database client"
}

repl({ db: prisma })
