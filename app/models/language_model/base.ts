import { Configuration, OpenAIApi } from "openai"

declare global {
    var __openai__: InstanceType<typeof OpenAIApi>
}

// Setup an instance of the LLM api
const configuration = new Configuration({
    apiKey: process.env.OPENAI_KEY,
})
global.__openai__ = new OpenAIApi(configuration)

export function openai() {
    return global.__openai__
}