import { IconCheck, IconX } from "@tabler/icons"

import type { PasswordInputProps } from "@mantine/core"
import {
  Box,
  Center,
  Group,
  PasswordInput,
  Progress,
  Text,
  createStyles,
} from "@mantine/core"
import { useInputState } from "@mantine/hooks"

function PasswordRequirement({
  meets,
  label,
}: {
  meets: boolean
  label: string
}) {
  return (
    <Text color={meets ? "teal" : "red"} mt={5} size="sm">
      <Center inline>
        {meets ? (
          <IconCheck size={14} stroke={1.5} />
        ) : (
          <IconX size={14} stroke={1.5} />
        )}
        <Box ml={7}>{label}</Box>
      </Center>
    </Text>
  )
}

const requirements = [
  { re: /[0-9]/, label: "Includes number" },
  { re: /[a-z]/, label: "Includes lowercase letter" },
  { re: /[A-Z]/, label: "Includes uppercase letter" },
  { re: /[$&+,:;=?@#|'<>.^*()%!-]/, label: "Includes special symbol" },
]

function getStrength(password: string) {
  let multiplier = password.length > 5 ? 0 : 1

  requirements.forEach((requirement) => {
    if (!requirement.re.test(password)) {
      multiplier += 1
    }
  })

  return Math.max(100 - (100 / (requirements.length + 1)) * multiplier, 0)
}

const useStyles = createStyles((theme) => ({
  passwordStrength: {
    transitionProperty: "max-height",
    transitionDuration: "1s",
    transitionTimingFunction: "cubic-bezier(0.175, 0.885, 0.32, 1.275)",
    maxHeight: "0px",
    overflow: "hidden",
  },
  passwordStrengthShow: {
    maxHeight: "400px",
  },
}))

export function PasswordWithStrength(args: PasswordInputProps) {
  const [value, setValue] = useInputState("")
  const strength = getStrength(value)
  const checks = requirements.map((requirement, index) => (
    <PasswordRequirement
      key={index}
      label={requirement.label}
      meets={requirement.re.test(value)}
    />
  ))
  const { classes } = useStyles()

  const bars = Array(4)
    .fill(0)
    .map((_, index) => (
      <Progress
        styles={{ bar: { transitionDuration: "0ms" } }}
        value={
          value.length > 0 && index === 0
            ? 100
            : strength >= ((index + 1) / 4) * 100
            ? 100
            : 0
        }
        color={strength > 80 ? "teal" : strength > 50 ? "yellow" : "red"}
        key={index}
        size={4}
      />
    ))

  const pwStrengthClasses = `${classes.passwordStrength} ${
    value !== "" ? classes.passwordStrengthShow : ""
  }`

  return (
    <div>
      <PasswordInput {...args} onChange={setValue} required />

      <div className={pwStrengthClasses}>
        <Group spacing={5} grow mt="xs" mb="md">
          {bars}
        </Group>

        <PasswordRequirement
          label="Has at least 6 characters"
          meets={value.length > 5}
        />
        {checks}
      </div>
    </div>
  )
}
