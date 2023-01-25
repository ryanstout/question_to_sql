import { IconSearch } from "@tabler/icons"
import {
  Form
} from "@remix-run/react"

import {useState} from "react"

import { Center, Grid, Loader, TextInput, Title } from "@mantine/core"

export default function Search({ question }: { question: string }) {
  
  const [isLoading, setIsLoading] = useState(false)  
  const [userQuery, setUserQuery] = useState("");

  let loader;

  if(isLoading && question){
    setIsLoading(false);
  }

  if(isLoading){
    loader = (
      <Loader size="xs" />
    );
  }

  const handleSubmit = () => {
    setIsLoading(true);
    setUserQuery('');
  }

  return (
    <>
      <main>
        <Grid>
          <Grid.Col span={4} offset={4}>
            <Form 
              action="?index" 
              method="post"
              onSubmit={(e) => {handleSubmit()}}
            >
              <TextInput
                width={100}
                name="q"
                rightSection={loader}
                onChange={(e) => setUserQuery(e.target.value)}
                value={userQuery}
                icon={<IconSearch size={18} />}
              />
            </Form>
          </Grid.Col>
        </Grid>
      </main>
    </>
  )
}
