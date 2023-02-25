import { Link } from "@remix-run/react"

import { Box, Button, Grid, Menu } from "@mantine/core"
import { useClipboard } from "@mantine/hooks"

import processDownload from "~/lib/downloader.client"
import type { QuestionResult } from "~/lib/question.server"

import {
  IconBraces,
  IconCloudDownload,
  IconFileSpreadsheet,
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
  //TODO Create other share options (e.g. Slack, Teams, etc)
  //TODO Create other export options (e.g. Google Sheets, etc)
  // TODO should disable actions when loading
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
          {!questionResult ? null : (
            <Button.Group>
              <QuestionActionDownloadMenu questionResult={questionResult} />
              <QuestionActionShareMenu />
            </Button.Group>
          )}
        </Grid.Col>
      </Grid>
    </Box>
  )
}

function QuestionActionDownloadMenu({
  questionResult,
}: {
  questionResult: QuestionResult | null
}) {
  return (
    <Menu trigger="hover" shadow="md" width={200}>
      <Menu.Target>
        <Button variant="subtle" color="dark">
          <IconCloudDownload />
        </Button>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>Download Options</Menu.Label>
        <DownloadMenuItem
          fileType={"json"}
          questionResult={questionResult}
          displayIcon={<IconBraces size={16} />}
        />
        <DownloadMenuItem
          fileType={"csv"}
          questionResult={questionResult}
          displayIcon={<IconFileSpreadsheet size={16} />}
        />
      </Menu.Dropdown>
    </Menu>
  )
}

function DownloadMenuItem({
  fileType,
  questionResult,
  displayIcon,
}: {
  fileType: string
  questionResult: QuestionResult | null
  displayIcon: React.ReactNode
}) {
  return (
    <Menu.Item
      onClick={() => {
        processDownload(
          fileType,
          questionResult?.data,
          questionResult?.question.question.split(" ").join("_")
        )
      }}
      icon={displayIcon}
    >
      {getMenuDisplayTitleFromFileType(fileType)}
    </Menu.Item>
  )
}

function getMenuDisplayTitleFromFileType(fileType: string) {
  switch (fileType) {
    case "json":
      return "as JSON"
    case "csv":
      return "as CSV"
    default:
      return ""
  }
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
