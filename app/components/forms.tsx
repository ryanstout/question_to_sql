import { z } from "zod"
import { zx } from "zodix"

import { useNavigation, useTransition } from "@remix-run/react"

export const ACTION_NAME_LABEL = "actionName"

export function FormActionName({ actionName }: { actionName: string }) {
  return <input type="hidden" name={ACTION_NAME_LABEL} value={actionName} />
}

// TODO is this a good pattern? not sure. It definitely needs a different name
export function useIsLoading() {
  const transition = useTransition()
  const navigation = useNavigation()
  const isLoading =
    navigation.state == "submitting" || transition.state != "idle"
  return isLoading
}

// TODO not totally sure if this is a great pattern to run multiple `parseForm` but
//      in areas where we need to share the code it's a good practice

export async function parseQuestionText(request: Request) {
  const minQuestionLength = 10

  const { questionText } = await zx.parseForm(request, {
    questionText: z
      .string()
      .trim()
      .min(minQuestionLength, "Question too short, add some more details!"),
  })

  return questionText
}

export async function parseActionName(request: Request) {
  const { actionName } = await zx.parseForm(request, {
    actionName: z.string(),
  })

  return actionName
}
