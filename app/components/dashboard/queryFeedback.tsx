import { IconPlus } from "@tabler/icons"
import { Accordion, Grid, Text } from "@mantine/core"

type QueryFeedback = {
  q: string
  sql: string
}

export default function QueryFeedback({ feedback }: { feedback: QueryFeedback }) {
  
  let queryFeedbackFragment = (
    <></>
  );

  if(feedback.q && feedback.sql){
    queryFeedbackFragment = (
      <Grid>
        <Grid.Col span={4} offset={4}>
      <Accordion 
        defaultValue="queryFeedback"
        chevron={<IconPlus size={16} />}
        styles={{
          chevron: {
            '&[data-rotate]': {
              transform: 'rotate(45deg)',
            },
          },
          item: {
            border: '1px solid #ededed',
          }
        }}
      >
       <Accordion.Item value="queryFeedback">
           <Accordion.Control>
             <Text>
              {feedback.q}
             </Text>
           </Accordion.Control>
           <Accordion.Panel>
              <Text>
              {feedback.sql}
              </Text>
           </Accordion.Panel>
       </Accordion.Item>
       </Accordion>
       </Grid.Col>
   </Grid>

    )
  }

  return (
    queryFeedbackFragment
  )
}
