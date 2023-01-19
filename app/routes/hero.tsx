import { IconCheck } from "@tabler/icons"

import { Link } from "@remix-run/react"

import {
  Button,
  Container,
  Group,
  List,
  Text,
  ThemeIcon,
  Title,
  createStyles,
} from "@mantine/core"

const useStyles = createStyles((theme) => ({
  inner: {
    display: "flex",
    justifyContent: "space-between",
    paddingTop: theme.spacing.xl * 4,
    paddingBottom: theme.spacing.xl * 4,
  },

  content: {
    maxWidth: 480,
    marginRight: theme.spacing.xl * 3,

    [theme.fn.smallerThan("md")]: {
      maxWidth: "100%",
      marginRight: 0,
    },
  },

  title: {
    color: theme.colorScheme === "dark" ? theme.white : theme.black,
    fontFamily: `Greycliff CF, ${theme.fontFamily}`,
    fontSize: 44,
    lineHeight: 1.2,
    fontWeight: 900,

    [theme.fn.smallerThan("xs")]: {
      fontSize: 28,
    },
  },

  control: {
    [theme.fn.smallerThan("xs")]: {
      flex: 1,
    },
  },

  image: {
    flex: 1,

    [theme.fn.smallerThan("md")]: {
      display: "none",
    },
  },

  highlight: {
    position: "relative",
    backgroundColor: theme.fn.variant({
      variant: "light",
      color: theme.primaryColor,
    }).background,
    borderRadius: theme.radius.sm,
    padding: "4px 12px",
  },
}))

export function Hero() {
  const { classes } = useStyles()
  return (
    <div>
      <Container>
        <div className={classes.inner}>
          <div className={classes.content}>
            <Title className={classes.title}>
              A <span className={classes.highlight}>better</span> way to <br />{" "}
              improve conversions
            </Title>
            <Text color="dimmed" mt="md">
              A/B testing helps you find the best landing page for all of your
              users. But you should be finding the best page for each user.
            </Text>

            <List
              mt={30}
              spacing="sm"
              size="sm"
              icon={
                <ThemeIcon size={20} radius="xl">
                  <IconCheck size={12} stroke={1.5} />
                </ThemeIcon>
              }
            >
              <List.Item>
                <b>Machine learning</b> optimizes each users expeience for
                maximum conversions
              </List.Item>
              <List.Item>
                <b>Large language models</b> help create variants that
                outperform human copy any project
              </List.Item>
              <List.Item>
                <b>One line of Javascript</b> is all it takes to get started
              </List.Item>
            </List>

            <Group mt={30}>
              <Button
                variant="gradient"
                component={Link}
                to="/sites"
                radius="xl"
                size="md"
                className={classes.control}
              >
                Get started
              </Button>
              <Button
                component={Link}
                to="/sites/new"
                variant="default"
                radius="xl"
                size="md"
                className={classes.control}
              >
                Learn More
              </Button>
            </Group>
          </div>
        </div>
      </Container>
    </div>
  )
}
