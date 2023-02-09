// TODO I don't understand what this is doing and why it is necessary
import { useField } from "remix-validated-form"

import { TextInput } from "@mantine/core"

export type FieldOwnInputProps<T extends React.ElementType> = {
  component?: T
  name: string
  label: string
  placeholder?: string
}

type FieldInputProps<T extends React.ElementType> = FieldOwnInputProps<T> &
  Omit<React.ComponentProps<T>, keyof FieldOwnInputProps<T>>

export const Field = <T extends React.ElementType>({
  component,
  name,
  label,
  placeholder,
  ...otherProps
}: FieldInputProps<T>) => {
  const { error, getInputProps } = useField(name)

  const Component = component || TextInput
  return (
    <Component
      withAsterisk
      label={label}
      placeholder={placeholder || label}
      error={error}
      // TODO this is broken without passing the generic https://github.com/airjp73/remix-validated-form/issues/81
      // @ts-ignore
      {...getInputProps({ id: name })}
      {...otherProps}
    />
  )
}
