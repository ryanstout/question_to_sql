import { useNavigation, useTransition } from "@remix-run/react"

export function FormActionName({ actionName }: { actionName: string }) {
  return <input type="hidden" name="actionName" value={actionName} />
}

// TODO is this a good pattern? not sure. It definitely needs a different name
export function useIsLoading() {
  const transition = useTransition()
  const navigation = useNavigation()
  const isLoading =
    navigation.state == "submitting" || transition.state != "idle"
  return isLoading
}
