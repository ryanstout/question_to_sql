from prisma import Prisma

DATABASE = None


def application_database_connection():
    global DATABASE

    if DATABASE is None:
        DATABASE = Prisma()
        DATABASE.connect()
    return DATABASE
