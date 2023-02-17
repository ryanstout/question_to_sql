import { Link } from "@remix-run/react"

import { Box, Button, Divider, Grid, Menu } from "@mantine/core"
import { useClipboard } from "@mantine/hooks"

import type { QuestionResult } from "~/lib/question.server"

import {
  IconBraces,
  IconCloudDownload,
  IconHistory,
  IconLink,
  IconShare,
} from "@tabler/icons-react"

export default function QuestionActionHeader({
  isLoading,
  questionResult,
}: {
  isLoading: boolean
  questionResult: QuestionResult | null
}) {
  //TODO Create other share options
  //TODO Create export as Google Sheets, XLSX, etc

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
        <Grid.Col span={9}></Grid.Col>
        <Grid.Col span={1}>
          <Button.Group>
            <QuestionActionDownloadMenu questionResult={questionResult} />
            <QuestionActionShareMenu />
          </Button.Group>
        </Grid.Col>
      </Grid>

      <Divider my="sm" variant="dotted" />
    </Box>
  )
}

function QuestionActionDownloadMenu({
  questionResult,
}: {
  questionResult: QuestionResult | null
}) {
  //TODO add support to download as CSV
  return (
    <Menu trigger="hover" shadow="md" width={200}>
      <Menu.Target>
        <Button variant="subtle" color="dark">
          <IconCloudDownload />
        </Button>
      </Menu.Target>

      <Menu.Dropdown>
        <Menu.Label>Download Options</Menu.Label>
        <Menu.Item
          onClick={() => {
            downloadResultAsJSON(
              questionResult?.data,
              questionResult?.question.question.split(" ").join("_")
            )
          }}
          icon={<IconBraces size={16} />}
        >
          as JSON
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  )
}

function downloadResultAsJSON(exportObj: any, exportName: string | undefined) {
  if (exportName == undefined) {
    return
  }

  const dataStr =
    "data:text/json;charset=utf-8," +
    encodeURIComponent(JSON.stringify(exportObj))
  let downloadAnchorNode = document.createElement("a")
  downloadAnchorNode.setAttribute("href", dataStr)
  downloadAnchorNode.setAttribute("download", exportName + ".json")
  document.body.appendChild(downloadAnchorNode)
  downloadAnchorNode.click()
  downloadAnchorNode.remove()
}

function QuestionActionShareMenu() {
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
