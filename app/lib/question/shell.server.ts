function rootDirectory() {
  return path.resolve(__filename + "/../../..")
}

function pythonCommand() {
  return path.resolve(rootDirectory() + "/bin/python-wrapper")
}

function escapeShell(cmd: string) {
  return '"' + cmd.replace(/(["'$`\\])/g, "\\$1") + '"'
}

export async function questionToSqlViaShell() {
  return new Promise((resolve, reject) => {
    const pythonPath = pythonCommand()
    log.debug("sending question to python", {
      question: naturalQuestion,
      path: pythonPath,
    })

    PythonShell.run(
      "python/answer.py",
      {
        pythonPath: pythonPath,
        mode: "text",
        cwd: rootDirectory(),
        args: [
          "--data-source-id",
          dataSourceId.toString(),
          "--question",
          escapeShell(naturalQuestion),
        ],
      },
      (err, results) => {
        if (err) {
          log.error("error running python", { results })
          reject(err)
        } else {
          resolve(results!.join("\n"))
        }
      }
    )

}