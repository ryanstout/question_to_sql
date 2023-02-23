import { useEffect, useRef, useState } from "react"

import { Form, useSubmit } from "@remix-run/react"

import { Box, Text, createStyles } from "@mantine/core"
import { getHotkeyHandler } from "@mantine/hooks"

import { FormActionName } from "~/components/forms"
import { QuestionActions } from "~/routes/question/($questionId)"

import { sql } from "@codemirror/lang-sql"
import { EditorView } from "@codemirror/view"
import CodeMirror from "@uiw/react-codemirror"

function SQLKeyboardShortcutOverlay() {
  return (
    <Box
      sx={{
        position: "relative",
        bottom: "25px",
      }}
    >
      <Text c="dimmed" align="center">
        <span
          style={{
            padding: "6px",
            backgroundColor: "rgba(128,128,128,0.1)",
          }}
        >
          Press Shift+Enter to execute an updated query
        </span>
      </Text>
    </Box>
  )
}

const useStyles = createStyles((theme) => ({
  sqlViewer: {
    border: "1px",
    borderStyle: "solid",
    borderColor: theme.colors.gray[3],
  },
}))

export default function SQLDisplay({
  isLoading,
  sqlText,
  additionalFields,
}: {
  isLoading: boolean
  sqlText: string | null
  additionalFields?: React.ReactNode
}) {
  const submit = useSubmit()

  // called when the user does SHIFT+Enter, updates the sql in the db
  // which will run the new query
  const updateSqlQuery = () => {
    submit(formRef.current)
  }

  // TODO the HotKeyItem[] used with `getHotkeyHandler` is not exported and differs from the other HotKeyItem config
  const hotKeyConfig: any = [["shift+Enter", updateSqlQuery]]

  const [userSQL, setSQL] = useState<string>(sqlText ?? "")
  const formRef = useRef(null)

  useEffect(() => {
    setSQL(sqlText || "")
  }, [sqlText])

  const { classes } = useStyles()

  return (
    <Form ref={formRef} method="post">
      <FormActionName actionName={QuestionActions.UPDATE} />
      <input type="hidden" name="userSql" value={userSQL} />
      {additionalFields}
      <CodeMirror
        height="275px"
        className={classes.sqlViewer}
        value={userSQL}
        extensions={[sql({}), EditorView.lineWrapping]}
        onChange={(e) => setSQL(e)}
        onKeyDownCapture={getHotkeyHandler(hotKeyConfig)}
        readOnly={isLoading}
      />

      <SQLKeyboardShortcutOverlay />
    </Form>
  )
}
