import { openai } from "./base";
import { promptForQuestion } from "./prompt.server";
import topenai from "@tectalic/openai";
import fs from "fs";
import { File } from "openai/dist/models";
import { Readable } from "stream";

import { prisma } from "~/db.server";

async function getTrainExamples(userId: number) {
  let questionGroups = await prisma.questionGroup.findMany({
    where: { userId },
  });

  let examples = [];
  for await (const questionGroup of questionGroups) {
    // Find the question that is marked as correct
    const correctQuestion = await prisma.question.findFirst({
      where: {
        questionGroupId: questionGroup.id,
        correctState: 1,
      },
    });

    // if one of the questions has been marked as correct for this
    // group
    if (correctQuestion) {
      // get the individual questions
      const questions = await prisma.question.findMany({
        where: { questionGroupId: questionGroup.id },
      });

      for await (const question of questions) {
        examples.push({
          prompt: await promptForQuestion(question.question),
          // Use the correect questions sql as the completion for all
          completion: correctQuestion.userSql,
        });
      }
    }
  }

  return examples;
}

export async function train(userId: number) {
  const openaiInst = openai();

  // const examples = await getTrainExamples(userId)
  const examples = [
    { prompt: "How many orders?", completion: "SELECT COUNT(*) FROM orders" },
  ];
  // const exampleJson = JSON.stringify(examples)

  // JsonL is one json object per line

  const exampleJsonL = [] as string[];
  examples.forEach((example) => {
    exampleJsonL.push(JSON.stringify(example));
  });

  // console.log('exampleJson', exampleJson)

  // const fineTuneStream = new Readable()
  // fineTuneStream.push(exampleJson)

  console.log("example JSONL ", exampleJsonL.join("\n") + "\n");

  const fineTuneStream = fs.createReadStream("temp.jsonl");
  // const fineTuneStream: any = Readable.from(exampleJsonL.join("\n") + "\n")
  // fineTuneStream.path = 'temp.jsonl' // have to give it a path for the api

  console.log("create file", exampleJsonL.length);
  // try {
  const openaiFile = await openaiInst.createFile(
    fineTuneStream as any, // There's a File type that doesn't exist bug here: https://github.com/openai/openai-node/issues/25
    "fine-tune"
  );

  console.log(
    "created file:",
    openaiFile.data.id,
    " filename: ",
    openaiFile.data.filename
  );

  const fileId = openaiFile.data.id;

  const modelSuffix = `${userId}-${Date.now()}`;

  const tapi = topenai(process.env.OPENAI_KEY);

  const resp = tapi.fineTunes.create({
    model: "davinci",
    training_file: fileId,
  });

  // const resp = await openaiInst.createFineTune({
  //     model: "davinci-codex",
  //     training_file: fileId,
  //     suffix: modelSuffix
  // })

  console.log("response: ", resp.statusText, resp.headers, resp.data);

  console.log("training started");

  // TODO: wait until the fine tuned model is done training

  // Update the model to point to the latest fine-tuned model

  await prisma.user.update({
    data: {
      fineTuneName: modelSuffix,
    },
    where: { id: userId },
  });
  // }
  // catch (e) {
  //     console.log('error: ', e.toString())
  // }
}
