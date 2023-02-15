import { Link } from "@remix-run/react"

import { Box, Button, Divider, Grid, Group, Menu } from "@mantine/core"
import { useClipboard } from "@mantine/hooks"

import type { Question } from "@prisma/client"

import { IconHistory, IconLink, IconShare } from "@tabler/icons-react"

export default function QuestionActionHeader({
  isLoading,
  questionRecord,
}: {
  isLoading: boolean
  questionRecord: Question | null
}) {
  //TODO Create download action
  //TODO Create other share options

  return (
    <Box>
      <Grid>
        <Grid.Col span={1}>
          <Link to="/history">
            <Button variant="subtle" leftIcon={<IconHistory size={18} />}>
              History
            </Button>
          </Link>
        </Grid.Col>
        <Grid.Col span={10}></Grid.Col>
        <Grid.Col span={1}>
          <Group>
            <QuestionActionShareHeader />
          </Group>
        </Grid.Col>
      </Grid>

      <Divider my="sm" variant="dotted" />
    </Box>
  )
}

function QuestionActionShareHeader() {
  const clipboard = useClipboard({ timeout: 700 })

  return (
    <Menu trigger="hover" shadow="md" width={200}>
      <Menu.Target>
        <Button variant="subtle" color={clipboard.copied ? "orange" : "dark"}>
          {clipboard.copied ? "Copied" : <IconShare />}
        </Button>
      </Menu.Target>

      <Menu.Dropdown>
        <Menu.Label>Share</Menu.Label>
        <Menu.Item
          onClick={() => clipboard.copy(window.location.href)}
          icon={<IconLink size={16} />}
        >
          Copy Link
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  )
}
