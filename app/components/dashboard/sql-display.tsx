import { useEffect, useState } from "react"

import { useSubmit } from "@remix-run/react"

import { Box, Text } from "@mantine/core"
import { getHotkeyHandler } from "@mantine/hooks"

import type { Question } from "@prisma/client"

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
            padding: "5px",
            backgroundColor: "rgba(128,128,128,0.1)",
          }}
        >
          Press Shift+Enter to execute an updated query
        </span>
      </Text>
    </Box>
  )
}

export default function SQLDisplay({
  isLoading,
  questionRecord,
}: {
  isLoading: boolean
  questionRecord?: Question
}) {
  const submitSqlQuery = useSubmit()

  // called when the user does SHIFT+Enter, updates the sql in the db
  // which will run the new query
  const updateSqlQuery = () => {
    if (questionRecord) {
      submitSqlQuery(
        {
          actionName: QuestionActions.UPDATE,
          questionId: questionRecord.id.toString(),
          userSql: userSQL,
        },
        { method: "post" }
      )
    }
  }

  const hotKeyConfig = [["shift+Enter", updateSqlQuery]]

  const [userSQL, setSQL] = useState(questionRecord?.sql || "")

  useEffect(() => {
    if (questionRecord) {
      const latestSQL = questionRecord.userSql ?? questionRecord.sql

      // TODO when could this case occur? Let's track via sentry
      if (latestSQL) {
        setSQL(latestSQL)
      }
    }
  }, [questionRecord])

  return (
    <>
      <CodeMirror
        height="275px"
        value={userSQL}
        extensions={[sql({}), EditorView.lineWrapping]}
        onChange={(e) => setSQL(e)}
        onKeyDownCapture={getHotkeyHandler(hotKeyConfig)}
      />

      <SQLKeyboardShortcutOverlay />
    </>
  )
}
