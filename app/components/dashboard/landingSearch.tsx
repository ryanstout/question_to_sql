import { Grid, Loader, TextInput } from "@mantine/core"
import {
  Form
} from "@remix-run/react"
import { IconSearch } from "@tabler/icons"
import { useState } from "react"



export default function LandingSearch({ question }: { question: string }) {
  
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
              action="/admin?index" 
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
