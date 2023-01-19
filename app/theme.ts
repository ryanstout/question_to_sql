import type { MantineThemeOverride } from "@mantine/core"

export const theme: MantineThemeOverride = {
  colorScheme: "light",
  // fontFamily: 'Open Sans',
  // defaultRadius: 'sm'
  defaultGradient: {
    from: "orange",
    to: "red",
    deg: 45,
  },

  // primaryShade: 6

  // primaryColor: "orange",

  fontSizes: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 22,
  },
}
