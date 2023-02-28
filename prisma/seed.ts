import bcrypt from "bcryptjs"

import { DataSourceType, PrismaClient } from "@prisma/client"

const prisma = new PrismaClient()

async function seed() {
  const email = "rachel@remix.run"
  const name = "test account"

  // cleanup the existing database
  await prisma.user.delete({ where: { email } }).catch(() => {
    // no worries if it doesn't exist yet
  })

  const hashedPassword = await bcrypt.hash("seedpassword1", 10)

  const business = await prisma.business.create({
    data: { name: "Great Business" },
  })

  const user = await prisma.user.create({
    data: {
      businessId: business.id,
      email,
      name,
      password: {
        create: {
          hash: hashedPassword,
        },
      },
    },
  })

  // create a data source for hacking
  const dataSource = await prisma.dataSource.create({
    data: {
      name: "Personal Snowflake",
      businessId: business.id,
      type: DataSourceType.SNOWFLAKE,
      credentials: {
        // set to empty string so logic that relies on these fields existing works, even if the values are useless
        // this is helpful for tests which have recorded values for snowflake
        account: process.env.SNOWFLAKE_ACCOUNT || "",
        username: process.env.SNOWFLAKE_USERNAME || "",
        password: process.env.SNOWFLAKE_PASSWORD || "",
        database: process.env.SNOWFLAKE_DATABASE || "",
        schema: process.env.SNOWFLAKE_SCHEMA || "",
        warehouse: process.env.SNOWFLAKE_WAREHOUSE || "",
      },
    },
  })

  console.log(`Database has been seeded. 🌱`)
}

seed()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
