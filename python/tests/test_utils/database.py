from python.utils.db import application_database_connection

db = application_database_connection()


def teardown():
    """
    Use prisma to truncate all tables
    """
    db.datasourcetablecolumn.delete_many()
    db.datasourcetabledescription.delete_many()
    db.datasource.delete_many()
