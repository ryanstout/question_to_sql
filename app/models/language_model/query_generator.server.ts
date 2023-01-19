// import OpenAI from 'openai-api'
import { openai } from "./base";
import { Configuration, OpenAIApi } from "openai";
import { PythonShell } from "python-shell";
import { format } from "sql-formatter";

import { promptForQuestion } from "~/models/language_model/prompt.server";

export async function EnhanceSqlQuery(query: string): Promise<string> {
  // return query
  return new Promise((resolve, reject) => {
    // const { stdout, stderr } = await exec("python lib/sql_enhance.py")
    let shell = new PythonShell("lib/sql_enhance.py", { mode: "text" });
    let output = [] as string[];
    shell.on("message", (message) => {
      console.log("message", message);
      output.push(message);
    });
    shell.send(query);
    shell.end(function (err, code, signal) {
      // if (err) throw err;
      if (err) {
        reject(err);
      }

      let result = output.join("\n");

      result = format(result, { language: "postgresql" });

      resolve(result);
    });
  });
}

export async function GenerateSqlQuery(query: string): Promise<string> {
  // return Promise.resolve("SELECT COUNT(*)\nFROM orders\nWHERE created_at >= '2019-12-01'\nAND created_at < '2020-01-01'\nAND pledge_level = 'Arsenal 2 Standard'")

  // return Promise.resolve(`SELECT date_trunc('month', orders.created_at) AS month, orders.card_brand, COUNT(*) AS count FROM orders WHERE orders.card_brand IS NOT NULL GROUP BY month, orders.card_brand ORDER BY month, orders.card_brand;`)
  // return Promise.resolve(`SELECT to_char(created_at, 'YYYY-MM') AS month, count(*) AS orders
  // FROM orders
  // WHERE created_at > '2020-01-01'
  // GROUP BY month
  // ORDER BY month;`)
  const prompt = await promptForQuestion(query);

  const t1 = new Date().getTime();
  let response;

  // TODO: exponential backoff
  for (let i = 0; i < 10; i++) {
    try {
      response = await openai().createCompletion({
        model: "code-davinci-002",
        prompt: prompt,
        max_tokens: 1024, // was 256
        temperature: 0.0,
        top_p: 1,
        presence_penalty: 0,
        frequency_penalty: 0,
        best_of: 1,
        n: 1,
        stream: false,
        stop: [";", "\n\n"],
      });

      if (response.status > 200) {
        // try again
        console.log(
          "openai api failed with: ",
          response.status,
          " trying again..."
        );
      } else {
        // Successful request, return
        console.log("SELECT " + response.data.choices[0].text + ";");
        return "SELECT " + response.data.choices[0].text + ";";
      }
    } catch (e) {
      console.log(
        "caught: openai api failed with: ",
        response?.status,
        " trying again..."
      );
    }
  }

  throw new Error(`thrown: openai api failed with: ${response?.status}`);
}
