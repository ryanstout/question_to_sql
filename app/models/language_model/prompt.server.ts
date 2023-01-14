import { promises as fs } from 'fs'

export async function promptForQuestion(query: string) {
    // TODO: Hardcoded for now
    let prompt = (await fs.readFile('prisma/test_schema.sql')).toString()
    prompt += "\n\n-- " + query + "\nSELECT "
    // console.log('prompt: ', prompt)

    return prompt
}
