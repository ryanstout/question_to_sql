import { useField } from "remix-validated-form"

import { TextInput } from "@mantine/core"

export const FieldDefaultAsType = "text" as const
export type FieldDefaultAsType = typeof FieldDefaultAsType

export type FieldOwnInputProps<T extends React.ElementType> = {
  component?: T
  name: string
  label: string
  placeholder?: string
}

type FieldInputProps<T extends React.ElementType> = FieldOwnInputProps<T> &
  Omit<React.ComponentProps<T>, keyof FieldOwnInputProps<T>>

export const Field = <T extends React.ElementType = FieldDefaultAsType>({
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
      {...getInputProps({ id: name })}
      {...otherProps}
    />
  )
}
