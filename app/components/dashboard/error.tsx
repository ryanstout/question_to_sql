import { Link } from "@remix-run/react"

import { Button, Center, Grid, Stack, Text } from "@mantine/core"

import { IconAlertTriangle, IconArrowLeft } from "@tabler/icons-react"

export default function ErrorDisplay({
  returnLink,
  returnLinkText,
  userMessage,
}: {
  returnLink: string
  returnLinkText: string
  userMessage: string
}) {
  return (
    <Grid>
      <Grid.Col span={8} offset={2} p="lg">
        <Center>
          <Link to={returnLink}>
            <Button
              color="gray"
              variant="subtle"
              mb={6}
              leftIcon={<IconArrowLeft size={18} />}
            >
              {returnLinkText}
            </Button>
          </Link>
        </Center>
        <Stack
          sx={(theme) => ({
            padding: theme.spacing.xl,
            borderRadius: theme.radius.md,
            backgroundColor: theme.colors.yellow[7],
            cursor: "pointer",
          })}
        >
          <Center>
            <IconAlertTriangle color="white" size={40} />
          </Center>
          <Center>
            <Text c="white">{userMessage}</Text>
          </Center>
        </Stack>
      </Grid.Col>
    </Grid>
  )
}
