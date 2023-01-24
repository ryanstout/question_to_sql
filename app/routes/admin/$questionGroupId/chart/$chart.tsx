import type { Question, User } from "@prisma/client"
import {
  IconChartBar,
  IconChartLine,
  IconGrain,
  IconNotes,
} from "@tabler/icons"
import { useNavigate } from "react-router-dom"
import { zx } from "zodix"

import { useMatches, useParams, useSearchParams } from "@remix-run/react"
import type { LoaderFunction } from "@remix-run/server-runtime"

import { Box, Tabs, Title } from "@mantine/core"
import { Prism } from "@mantine/prism"
import type { BarDatum } from "@nivo/bar"
import { ResponsiveBar } from "@nivo/bar"
import type { Serie } from "@nivo/line"
import { ResponsiveLine } from "@nivo/line"

type GroupLoaderData = {
  questions: Question[]
  questionGroupId: number
  latestResult: string
}

type LoaderData = null

export let loader: LoaderFunction = async ({
  params,
  request,
}): Promise<LoaderData> => {
  return null
}

function LineChart({ type, data }: { type: string; data: Serie[] }) {
  if (!data || !data[0]) {
    return <div>no data</div>
  }
  // const keys = Object.keys(data[0])

  return <div>WIP</div>
  return (
    <div style={{ height: "500px" }}>
      <Title>Chart</Title>
      <ResponsiveLine
        data={data}
        margin={{ top: 50, right: 130, bottom: 50, left: 80 }}
        colors={{ scheme: "nivo" }}
      />
    </div>
  )
}

function BarChart({ type, data }: { type: string; data: BarDatum[] }) {
  if (!data || !data[0]) {
    return <div>no data</div>
  }
  const keys = Object.keys(data[0])

  return (
    <div style={{ height: "500px" }}>
      <Title>Chart</Title>
      <ResponsiveBar
        data={data}
        keys={keys.slice(1)}
        indexBy={keys[0]}
        enableGridX={false}
        enableLabel={false}
        padding={0.2}
        margin={{ top: 50, right: 130, bottom: 50, left: 80 }}
        axisTop={null}
        axisRight={null}
        axisBottom={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 70,
          legend: "country",
          legendPosition: "middle",
          legendOffset: 32,
        }}
        axisLeft={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 0,
          legend: "count",
          legendPosition: "middle",
          legendOffset: -60,
        }}
        colors={{ scheme: "nivo" }}
        colorBy={"indexValue"}
        legends={[
          {
            dataFrom: "keys",
            anchor: "top-left",
            direction: "row",
            justify: false,
            translateX: 120,
            translateY: -40,
            itemsSpacing: 2,
            itemWidth: 100,
            itemHeight: 20,
            itemDirection: "left-to-right",
            itemOpacity: 0.85,
            symbolSize: 20,
            effects: [
              {
                on: "hover",
                style: {
                  itemOpacity: 1,
                },
              },
            ],
          },
        ]}
      />
    </div>
  )
}

export default function VisualizeMethod() {
  const params = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  let question = searchParams.get("q") || ""

  const match = useMatches().find(
    (match) => match.id === "routes/query/$questionGroupId"
  )
  const data = match?.data ? (match.data as GroupLoaderData) : null

  const dataObj = data ? JSON.parse(data.latestResult || "{}") : null
  const latestResult = data ? data.latestResult : null

  function changeTab(value: string | null) {
    if (value) {
      navigate(
        `/query/${params.questionGroupId}/chart/${value}?q=` +
          encodeURIComponent(question),
        { preventScrollReset: true }
      )
    }
  }

  return (
    <Box>
      <Tabs defaultValue={params.chart} onTabChange={(v) => changeTab(v)}>
        <Tabs.List>
          <Tabs.Tab value="bar" icon={<IconChartBar size={14} />}>
            Bar
          </Tabs.Tab>
          <Tabs.Tab value="line" icon={<IconChartLine size={14} />}>
            Line
          </Tabs.Tab>
          <Tabs.Tab value="scatter" icon={<IconGrain size={14} />}>
            Scatter
          </Tabs.Tab>
          <Tabs.Tab value="raw" icon={<IconNotes size={14} />}>
            Raw
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="bar">
          <BarChart type={params.chart || "bar"} data={dataObj} />
        </Tabs.Panel>

        <Tabs.Panel value="line">
          <LineChart type={params.chart || "line"} data={dataObj} />
        </Tabs.Panel>

        <Tabs.Panel value="scatter"></Tabs.Panel>

        <Tabs.Panel value="raw">
          <Prism withLineNumbers language="json">
            {latestResult || ""}
          </Prism>
        </Tabs.Panel>
      </Tabs>
    </Box>
  )
}

export function ErrorBoundary({ error }) {
  return (
    <div>
      <h1>Error</h1>
      <p>{error.message}</p>
      <p>The stack trace is:</p>
      <pre>{error.stack}</pre>
    </div>
  )
}
