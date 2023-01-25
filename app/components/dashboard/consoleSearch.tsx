import {
    Box, createStyles, Flex, Loader, Paper, Table, Text, TextInput
} from "@mantine/core";
import {
    Form
} from "@remix-run/react";
import { IconSearch } from '@tabler/icons';



const useStyles = createStyles((theme) => ({
    currentQuestionFeedback: {
      borderTop: 0,
      borderLeft: 4,
      borderRight: 0,
      borderBottom: 0,
      borderStyle: "solid",
      borderColor: theme.colors.indigo[7]
    }
  }));
  

type QuestionState = {
    questionGroupId: string, 
    question: string, 
    previousQuestions: JSX.Element[],
    navigationState: string
  }

export default function ConsoleSearch({currentQuestionState} : {currentQuestionState: QuestionState}){

    const { classes } = useStyles();

    return (
        <Box>
        <Form method="post" action={`/admin/${currentQuestionState.questionGroupId}?q=${encodeURIComponent(currentQuestionState.question)}`}>
          <Flex>
            <input
              type="hidden"
              name="questionGroupId"
              value={currentQuestionState.questionGroupId}
            />
            <TextInput
              size="lg"
              w="100%"
              name="q"
              icon={<IconSearch size={18} />} 
              rightSection={currentQuestionState.navigationState === "submitting"  ? <Loader size="sm" /> : ""}
            />
          </Flex>
        </Form>
        <Paper shadow="xs" p="md" my="xs" className={classes.currentQuestionFeedback}>
          <Text>{currentQuestionState.question}</Text>
        </Paper>
        <Box sx={{ height: "90px", overflowY: "auto" }}>
          <Table p="sm">
            <tbody>{currentQuestionState.previousQuestions}</tbody>
          </Table>
        </Box>
      </Box>

    )
}