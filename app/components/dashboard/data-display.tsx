import beautify from "json-beautify"

import { Box, Tabs, Title } from "@mantine/core"
import { Prism } from "@mantine/prism"
import type { BarDatum } from "@nivo/bar"
import { ResponsiveBar } from "@nivo/bar"
import type { Serie } from "@nivo/line"

import { IconChartBar, IconChartLine, IconNotes } from "@tabler/icons"

function LineChart({ type, data }: { type: string; data: Serie[] }) {
  if (!data || !data[0]) {
    return <div>no data</div>
  }
  // const keys = Object.keys(data[0])

  return <div>WIP</div>
  // return (
  //   <div style={{ height: "500px" }}>
  //     <Title>Chart</Title>
  //     <ResponsiveLine
  //       data={data}
  //       margin={{ top: 50, right: 130, bottom: 50, left: 80 }}
  //       colors={{ scheme: "nivo" }}
  //     />
  //   </div>
  // )
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
        margin={{ top: 50, right: 130, bottom: 150, left: 80 }}
        axisTop={null}
        axisRight={null}
        axisBottom={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 70,
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

export default function DataDisplay({ data }: { data: any | null }) {
  if (!data) {
    return <></>
  }

  function changeTab(value: string | null) {
    if (value) {
      // TODO should update the URL with chart state
      // navigate(
      //   `/admin/${params.questionGroupId}/chart/${value}?q=` +
      //     encodeURIComponent(question),
      //   { preventScrollReset: true }
      // )
    }
  }

  const formattedJSON = beautify(data, null!, 2, 100)
  // TODO should format errors here like the old system
  // resultJson = beautify({ message: e!.toString(), error: e }, null!, 2, 100)

  return (
    <Box>
      <Tabs defaultValue="raw" onTabChange={(v) => changeTab(v)}>
        <Tabs.List>
          <Tabs.Tab value="raw" icon={<IconNotes size={14} />}>
            Raw
          </Tabs.Tab>
          <Tabs.Tab value="bar" icon={<IconChartBar size={14} />}>
            Bar
          </Tabs.Tab>
          <Tabs.Tab value="line" icon={<IconChartLine size={14} />}>
            Line
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="bar">
          <BarChart type={"bar"} data={data} />
        </Tabs.Panel>

        <Tabs.Panel value="line">
          <LineChart type={"line"} data={data} />
        </Tabs.Panel>

        {/* TODO there is some weird horizontal scrolling issue here */}
        <Tabs.Panel value="raw">
          <Prism withLineNumbers language="json">
            {formattedJSON}
          </Prism>
        </Tabs.Panel>
      </Tabs>
    </Box>
  )
}
